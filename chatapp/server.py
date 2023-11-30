import uvicorn
from dotenv import load_dotenv
import os
# import sys

# It is default
# if __name__ == "__main__":
#     uvicorn.run("chatapp.asgi:application", reload=True)


# pass the host and port as command-line arguments when running your Python script
# exaple:  python3 server.py 127.0.0.1 8000
# if __name__ == "__main__":
#     # Check if host and port are provided as command-line arguments
#     print("len(sys.argv): ", len(sys.argv))
#     print("sys.argv): ", sys.argv)
#     if len(sys.argv) != 3:
#         print("Usage: python3 server.py <host> <port>")
#         sys.exit(1)

#     host = sys.argv[1]
#     port = int(sys.argv[2])

#     uvicorn.run("chatapp.asgi:application", host=host, port=port, reload=True)



# pass the host and port from .env file when running your Python script
# .env
# SERVER_HOST=127.0.0.1
# SERVER_PORT=8000

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Get host and port from environment variables or use default values
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))

    uvicorn.run("chatapp.asgi:application", host=host, port=port, reload=True)