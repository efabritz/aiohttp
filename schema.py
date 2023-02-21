from pydantic import ValidationError
from pydantic import BaseModel
from errors import HttpError


class CreateUser(BaseModel):
    username: str
    password: str

def validate_create_user(json_data):
    try:
        user_schema = CreateUser(**json_data)
        return user_schema.dict()
    except ValidationError as er:
        raise HttpError(status_code=400, message=er.errors())