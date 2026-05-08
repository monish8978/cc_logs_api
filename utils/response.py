from fastapi.responses import JSONResponse


def success_response(
    message="Success",
    data=None,
    status_code=200
):
    """
    Common success response
    """

    return JSONResponse(
        status_code=status_code,
        content={
            "status": True,
            "message": message,
            "data": data or {}
        }
    )


def error_response(
    message="Something went wrong",
    status_code=400,
    error=None
):
    """
    Common error response
    """

    response = {
        "status": False,
        "message": message
    }

    if error:
        response["error"] = str(error)

    return JSONResponse(
        status_code=status_code,
        content=response
    )