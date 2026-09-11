import uvicorn
from pydantic import BaseModel, Field

from fastapi import Body, FastAPI, Path, Query

app = FastAPI()


class User(BaseModel):
    id: int = Field(default=..., title="id", description="id")


@app.post("/test/{id}")
def a(
    id: int = Path(..., description="用户id"),
    name: str = Query(default="用户", max_length=3),
    user: User = Body(default=...),
):
    return {"id": id, "name": name, "user": user}


if __name__ == "__main__":
    uvicorn.run("f1:app", host="localhost", port=9000, reload=True)
