#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def setup_text_service():
    print("Setting up Text Service...")
    service_dir = "services/text-service"
    
    # Create virtual environment
    if not run_command("python -m venv venv", cwd=service_dir):
        return False
    
    # Install dependencies
    if sys.platform == "win32":
        pip_cmd = "venv\\Scripts\\pip install -r requirements.txt"
        protoc_cmd = "venv\\Scripts\\python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. text_service.proto"
    else:
        pip_cmd = "venv/bin/pip install -r requirements.txt"
        protoc_cmd = "venv/bin/python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. text_service.proto"
    
    if not run_command(pip_cmd, cwd=service_dir):
        return False
    
    # Generate gRPC files
    if not run_command(protoc_cmd, cwd=service_dir):
        return False
    
    print("✅ Text Service setup complete!")
    return True

def setup_gateway():
    print("Setting up Gateway...")
    gateway_dir = "services/gateway"
    
    # Initialize Go module and download dependencies
    if not run_command("go mod tidy", cwd=gateway_dir):
        return False
    
    print("✅ Gateway setup complete!")
    return True

if __name__ == "__main__":
    print("🚀 Setting up Nimbus Platform...")
    
    if setup_text_service() and setup_gateway():
        print("\n✅ All services setup complete!")
        print("\nNext steps:")
        print("1. Run: docker-compose up -d")
        print("2. Test: curl -X POST http://localhost:8080/api/v1/text/process -H \"Content-Type: application/json\" -d '{\"text\": \"Hello Nimbus!\"}'")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)