import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("platform.log")
        ]
    )
    # Disable noisy logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
