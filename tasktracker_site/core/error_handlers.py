from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin

from .responses import RedirectToRefererResponse

from tasktracker_core.requests.controllers import (TaskTrackerError, 
                                                   PermissionDenied)

class HandleLibExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        
        if isinstance(exception, PermissionDenied):
            message = "Permission denied"
            messages.error(request, message)
            return RedirectToRefererResponse(request)

        if isinstance(exception, TaskTrackerError):
            message = str(exception)
            messages.error(request, message)
            return RedirectToRefererResponse(request)

        messages.error(request, 'Ooops! Something is going wrong')
        return RedirectToRefererResponse(request)
            

