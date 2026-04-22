package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"
)

type Gateway struct {
	redis      *redis.Client
	db         *sql.DB
	httpClient *http.Client
}

type TextRequest struct {
	Text string `json:"text"`
}

type TextResponse struct {
	ProcessedText string `json:"processed_text"`
	WordCount     int32  `json:"word_count"`
	CharCount     int32  `json:"char_count"`
}

type SentimentResponse struct {
	Sentiment    string  `json:"sentiment"`
	Confidence   float32 `json:"confidence"`
	Polarity     float32 `json:"polarity"`
	Subjectivity float32 `json:"subjectivity"`
}

type RequestLog struct {
	ID        int       `json:"id"`
	Endpoint  string    `json:"endpoint"`
	Method    string    `json:"method"`
	Timestamp time.Time `json:"timestamp"`
	Duration  int64     `json:"duration_ms"`
	Cached    bool      `json:"cached"`
}

func NewGateway() *Gateway {
	redisAddr := os.Getenv("REDIS_URL")
	if redisAddr == "" {
		redisAddr = "redis:6379"
	}
	rdb := redis.NewClient(&redis.Options{
		Addr:         redisAddr,
		PoolSize:     20,
		MinIdleConns: 5,
		MaxRetries:   3,
	})

	dbURL := os.Getenv("DB_URL")
	if dbURL == "" {
		log.Fatal("DB_URL environment variable is required")
	}
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	// Initialize database schema
	initDB(db)

	// HTTP client with connection pooling
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 10,
			IdleConnTimeout:     90 * time.Second,
		},
	}

	return &Gateway{
		redis:      rdb,
		db:         db,
		httpClient: httpClient,
	}
}

func initDB(db *sql.DB) {
	query := `
	CREATE TABLE IF NOT EXISTS request_logs (
		id SERIAL PRIMARY KEY,
		endpoint VARCHAR(255),
		method VARCHAR(10),
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		duration_ms BIGINT,
		cached BOOLEAN DEFAULT FALSE
	)`
	
	if _, err := db.Exec(query); err != nil {
		log.Printf("Failed to create table: %v", err)
	}
}

func (g *Gateway) logRequest(endpoint, method string, duration time.Duration, cached bool) {
	go func() {
		query := `INSERT INTO request_logs (endpoint, method, duration_ms, cached) VALUES ($1, $2, $3, $4)`
		_, err := g.db.Exec(query, endpoint, method, duration.Milliseconds(), cached)
		if err != nil {
			log.Printf("Failed to log request: %v", err)
		}
	}()
}

func (g *Gateway) processText(c *gin.Context) {
	start := time.Now()
	var req TextRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	cacheKey := fmt.Sprintf("text:%s", req.Text)
	
	// Try cache first
	cached, err := g.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var response TextResponse
		json.Unmarshal([]byte(cached), &response)
		g.logRequest("/api/v1/text/process", "POST", time.Since(start), true)
		c.JSON(http.StatusOK, response)
		return
	}

	// Call HTTP service
	reqBody, _ := json.Marshal(req)
	resp, err := g.httpClient.Post("http://text-service:8001/process", "application/json", bytes.NewBuffer(reqBody))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Service unavailable"})
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var response TextResponse
	json.Unmarshal(body, &response)

	// Cache with TTL
	responseJSON, _ := json.Marshal(response)
	g.redis.Set(context.Background(), cacheKey, responseJSON, 10*time.Minute)

	g.logRequest("/api/v1/text/process", "POST", time.Since(start), false)
	c.JSON(http.StatusOK, response)
}

func (g *Gateway) analyzeSentiment(c *gin.Context) {
	start := time.Now()
	var req TextRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	cacheKey := fmt.Sprintf("sentiment:%s", req.Text)
	
	// Try cache first
	cached, err := g.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var response SentimentResponse
		json.Unmarshal([]byte(cached), &response)
		g.logRequest("/api/v1/sentiment/analyze", "POST", time.Since(start), true)
		c.JSON(http.StatusOK, response)
		return
	}

	// Call HTTP service
	reqBody, _ := json.Marshal(req)
	resp, err := g.httpClient.Post("http://sentiment-service:8002/analyze", "application/json", bytes.NewBuffer(reqBody))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Service unavailable"})
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var response SentimentResponse
	json.Unmarshal(body, &response)

	// Cache with TTL
	responseJSON, _ := json.Marshal(response)
	g.redis.Set(context.Background(), cacheKey, responseJSON, 15*time.Minute)

	g.logRequest("/api/v1/sentiment/analyze", "POST", time.Since(start), false)
	c.JSON(http.StatusOK, response)
}

func (g *Gateway) getMetrics(c *gin.Context) {
	query := `
	SELECT 
		endpoint,
		COUNT(*) as total_requests,
		AVG(duration_ms) as avg_duration,
		COUNT(CASE WHEN cached = true THEN 1 END) as cached_requests,
		(COUNT(CASE WHEN cached = true THEN 1 END) * 100.0 / COUNT(*)) as cache_hit_rate
	FROM request_logs 
	WHERE timestamp > NOW() - INTERVAL '1 hour'
	GROUP BY endpoint`

	rows, err := g.db.Query(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get metrics"})
		return
	}
	defer rows.Close()

	var metrics []map[string]interface{}
	for rows.Next() {
		var endpoint string
		var totalReqs, cachedReqs int
		var avgDuration, cacheHitRate float64
		
		rows.Scan(&endpoint, &totalReqs, &avgDuration, &cachedReqs, &cacheHitRate)
		
		metrics = append(metrics, map[string]interface{}{
			"endpoint":       endpoint,
			"total_requests": totalReqs,
			"avg_duration":   avgDuration,
			"cached_requests": cachedReqs,
			"cache_hit_rate": cacheHitRate,
		})
	}

	c.JSON(http.StatusOK, gin.H{"metrics": metrics})
}

func (g *Gateway) health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"services": gin.H{
			"redis":    g.redis.Ping(context.Background()).Err() == nil,
			"postgres": g.db.Ping() == nil,
		},
		"version": "enhanced-v2.0",
	})
}

// proxyMultipart forwards multipart file uploads to a downstream service.
func (g *Gateway) proxyMultipart(target string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if err := c.Request.ParseMultipartForm(32 << 20); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid multipart form"})
			return
		}
		resp, err := g.httpClient.Post(target, c.Request.Header.Get("Content-Type"), c.Request.Body)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "image service unavailable"})
			return
		}
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)
		c.Data(resp.StatusCode, resp.Header.Get("Content-Type"), body)
	}
}

func (g *Gateway) streamChat(c *gin.Context) {
	var req TextRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	reqBody, _ := json.Marshal(req)
	resp, err := g.httpClient.Post("http://text-service:8001/stream", "application/json", bytes.NewBuffer(reqBody))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "text service unavailable"})
		return
	}
	defer resp.Body.Close()

	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("X-Accel-Buffering", "no")

	buf := make([]byte, 4096)
	for {
		n, err := resp.Body.Read(buf)
		if n > 0 {
			c.Writer.Write(buf[:n])
			c.Writer.Flush()
		}
		if err != nil {
			break
		}
	}
}

func main() {
	gateway := NewGateway()

	r := gin.Default()
	r.SetTrustedProxies([]string{"127.0.0.1", "::1"})

	r.Use(func(c *gin.Context) {
		start := time.Now()
		c.Next()
		log.Printf("%s %s - %v", c.Request.Method, c.Request.URL.Path, time.Since(start))
	})

	api := r.Group("/api/v1")
	{
		api.POST("/text/process", gateway.processText)
		api.POST("/sentiment/analyze", gateway.analyzeSentiment)
		api.POST("/chat/stream", gateway.streamChat)

		api.POST("/image/upload", gateway.proxyMultipart("http://image-service:8003/upload"))
		api.POST("/image/caption", gateway.proxyMultipart("http://image-service:8003/caption"))
		api.POST("/image/analyze", gateway.proxyMultipart("http://image-service:8003/analyze"))
		api.POST("/image/info", gateway.proxyMultipart("http://image-service:8003/info"))

		api.GET("/metrics", gateway.getMetrics)
		api.GET("/health", gateway.health)
	}

	log.Println("Enhanced Gateway starting on :8080")
	r.Run(":8080")
}