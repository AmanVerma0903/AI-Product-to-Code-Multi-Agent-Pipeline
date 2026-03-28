from fastapi import WebSocket
from typing import Dict, List, Any, Optional
import json


class ConnectionManager:
    def __init__(self):
        # run_id -> list of websocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.run_questions: Dict[int, List[str]] = {}
        self.run_feedback: Dict[int, str] = {}
        self.run_states: Dict[int, str] = {}   # running / paused

    # ---------------- CONNECT ----------------

    async def connect(self, run_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(run_id, []).append(websocket)

    def disconnect(self, run_id: int, websocket: WebSocket):
        if run_id in self.active_connections:
            if websocket in self.active_connections[run_id]:
                self.active_connections[run_id].remove(websocket)

    # ---------------- BROADCAST ----------------

    async def broadcast_to_run(self, run_id: int, message: str):
        """Send message only to clients connected to this run."""
        if run_id in self.active_connections:
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass

    # ---------------- MESSAGE HANDLER ----------------

    async def handle_message(
        self, run_id: int, message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        msg_type = message.get("type")

        # -------- QUESTION DURING RUN --------
        if msg_type == "question":
            question = message.get("text", "")
            self.run_questions.setdefault(run_id, []).append(question)

            return {
                "type": "question_received",
                "run_id": run_id,
                "question": question,
                "status": "stored"
            }

        # -------- USER FEEDBACK --------
        elif msg_type == "feedback":
            feedback = message.get("text", "")
            self.run_feedback[run_id] = feedback

            return {
                "type": "feedback_received",
                "run_id": run_id,
                "feedback": feedback,
                "status": "stored"
            }

        # -------- PAUSE REQUEST --------
        elif msg_type == "pause":
            self.run_states[run_id] = "paused"
            return {
                "type": "pause_ack",
                "run_id": run_id,
                "status": "paused"
            }

        # -------- RESUME REQUEST --------
        elif msg_type == "resume":
            self.run_states[run_id] = "running"
            return {
                "type": "resume_ack",
                "run_id": run_id,
                "status": "running"
            }

        return None

    # ---------------- STATE HELPERS ----------------

    def is_paused(self, run_id: int) -> bool:
        return self.run_states.get(run_id) == "paused"

    def get_run_questions(self, run_id: int) -> List[str]:
        return self.run_questions.get(run_id, [])

    def get_run_feedback(self, run_id: int) -> Optional[str]:
        return self.run_feedback.get(run_id)

    def clear_run_data(self, run_id: int):
        self.run_questions.pop(run_id, None)
        self.run_feedback.pop(run_id, None)
        self.run_states.pop(run_id, None)


ws_manager = ConnectionManager()