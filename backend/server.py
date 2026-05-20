import os
import sys
import logging
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Add workspace to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI App
app = FastAPI(title="KabaarAgent Backend", version="2.0.0")

# Enable CORS for local android development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom log collector handler
class StreamLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        self.logs.append(self.format(record))

# Setup Logger
logger = logging.getLogger("kabaar_agent")
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s")

# Request/Response schemas
class AppraisalRequest(BaseModel):
    description: str
    image_base64: Optional[str] = None
    latitude: Optional[float] = 33.60
    longitude: Optional[float] = 73.06

class ItemModel(BaseModel):
    material_type: str
    estimated_weight_kg: float
    purity_grade: str

class PipelineResponse(BaseModel):
    transaction_id: str
    items: List[ItemModel]
    valuation: float
    optimal_yard: Dict[str, Any]
    justification_log: str
    receipt: Dict[str, Any]
    execution_trace: List[str]

@app.get("/")
def read_root():
    return {"status": "running", "service": "KabaarAgent Backend API"}

@app.post("/api/pipeline", response_model=PipelineResponse)
async def run_pipeline(request: AppraisalRequest):
    # Setup log capturing for this request
    log_capture = StreamLogHandler()
    log_capture.setFormatter(log_formatter)
    logger.addHandler(log_capture)
    
    transaction_id = str(uuid.uuid4())
    logger.info(f"Pipeline started for Transaction ID: {transaction_id}")
    
    try:
        # Step 1: Appraiser Identification
        logger.info("Step 1/4 [Appraiser Identification]: Analyzing input data...")
        from backend.appraiser.appraiser import appraise
        input_val = request.image_base64 if (request.image_base64 and request.image_base64.strip()) else request.description
        items = appraise(input_val)
        logger.info(f"Appraisal finished. Extracted {len(items)} items: {items}")
        
        # Step 2: Arbitrage Index Matcher
        logger.info("Step 2/4 [Arbitrage Index Matcher]: Matching items with recycling yards...")
        from backend.arbitrage.arbitrage import run_arbitrage
        # Map item keys to what arbitrage expects: material, weight_kg
        mapped_items = [
            {"material": item["material_type"], "weight_kg": item["estimated_weight_kg"]}
            for item in items
        ]
        raw_arbitrage = run_arbitrage(mapped_items, request.latitude, request.longitude)
        
        # Map raw arbitrage to the format expected by the server and ops components
        arbitrage_result = {
            "total_valuation": raw_arbitrage.get("total_valuation_pkr", 0.0),
            "optimal_yard": raw_arbitrage.get("selected_yard") or {},
            "justification_log": raw_arbitrage.get("negotiation_justification_log", "")
        }
        logger.info(f"Arbitrage finished. Selected yard: {arbitrage_result.get('optimal_yard', {}).get('name')}")
        
        # Step 3: Operations Ledger Commit
        logger.info("Step 3/4 [Operations Ledger Commit]: Signing transaction and committing to ledger...")
        from backend.ops.ops import commit_transaction
        ops_result = commit_transaction(transaction_id, items, arbitrage_result)
        logger.info("Operations Ledger Commit finished. Receipt generated.")
        
        # Step 4: Finalize response
        logger.info("Step 4/4 [Pipeline Complete]: Returning results to mobile view.")
        
        # Capture and clean logs
        logger.removeHandler(log_capture)
        trace_logs = log_capture.logs
        
        return PipelineResponse(
            transaction_id=transaction_id,
            items=[ItemModel(**item) for item in items],
            valuation=arbitrage_result["total_valuation"],
            optimal_yard=arbitrage_result["optimal_yard"],
            justification_log=arbitrage_result["justification_log"],
            receipt=ops_result["receipt"],
            execution_trace=trace_logs
        )
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        logger.removeHandler(log_capture)
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
