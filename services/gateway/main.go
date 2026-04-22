package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"
)

type Gateway struct {
	redis *redis.Client
	db    *sql.DB
}

type TextRequest struct {
	Text string `json:"text"`
}

type TextResponse struct {
	ProcessedText string `json:"processed_text"`
	WordCount     int    `json:"word_count"`
	CharCount     int    `json:"char_count"`
}

type SentimentResponse struct {
	Sentiment    string  `json:"sentiment"`
	Confidence   float64 `json:"confidence"`
	Polarity     float64 `json:"polarity"`
	Subjectivity float64 `json:"subjectivity"`
}

func NewGateway() *Gateway {
	redisAddr := os.Getenv("REDIS_URL")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}
	rdb := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	dbURL := os.Getenv("DB_URL")
	if dbURL == "" {
		log.Fatal("DB_URL environment variable is required")
	}
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	return &Gateway{redis: rdb, db: db}
}

func (g *Gateway) processText(c *gin.Context) {
	var req TextRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	cacheKey := "text:" + req.Text
	cached, err := g.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var response TextResponse
		json.Unmarshal([]byte(cached), &response)
		c.JSON(http.StatusOK, response)
		return
	}

	// Call text service (simplified - would use gRPC in production)
	response := TextResponse{
		ProcessedText: req.Text,
		WordCount:     len(req.Text),
		CharCount:     len(req.Text),
	}

	responseJSON, _ := json.Marshal(response)
	g.redis.Set(context.Background(), cacheKey, responseJSON, 5*time.Minute)

	c.JSON(http.StatusOK, response)
}

func (g *Gateway) analyzeSentiment(c *gin.Context) {
	var req TextRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	cacheKey := "sentiment:" + req.Text
	cached, err := g.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var response SentimentResponse
		json.Unmarshal([]byte(cached), &response)
		c.JSON(http.StatusOK, response)
		return
	}

	// Call sentiment service (simplified - would use gRPC in production)
	response := SentimentResponse{
		Sentiment:    "positive",
		Confidence:   0.8,
		Polarity:     0.5,
		Subjectivity: 0.6,
	}

	responseJSON, _ := json.Marshal(response)
	g.redis.Set(context.Background(), cacheKey, responseJSON, 5*time.Minute)

	c.JSON(http.StatusOK, response)
}

func (g *Gateway) health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}

func main() {
	gateway := NewGateway()
	
	r := gin.Default()
	r.SetTrustedProxies([]string{"127.0.0.1", "::1"})
	
	api := r.Group("/api/v1")
	{
		api.POST("/text/process", gateway.processText)
		api.POST("/sentiment/analyze", gateway.analyzeSentiment)
		api.GET("/health", gateway.health)
	}

	log.Println("Gateway starting on :8080")
	r.Run(":8080")
}