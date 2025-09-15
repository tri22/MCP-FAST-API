# main.py
import uvicorn
from api import api  # api = FastAPI() trong file bạn gửi

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8080)