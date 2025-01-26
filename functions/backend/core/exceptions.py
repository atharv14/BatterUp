from fastapi import HTTPException, status

class PlayerNotFoundException(HTTPException):
    def __init__(self, player_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id} not found"
        )

class DatabaseException(HTTPException):
    def __init__(self, operation: str, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during {operation}: {detail}"
        )