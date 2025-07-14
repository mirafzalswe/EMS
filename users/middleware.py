# from django.shortcuts import redirect
# from django.urls import reverse
# from django.conf import settings

# class AuthenticationMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # List of paths that don't require authentication
#         public_paths = [
#             reverse('login'),
#             '/admin/login/',
#             '/static/',
#             '/media/',
#         ]

#         # Check if the current path is public
#         is_public_path = any(request.path.startswith(path) for path in public_paths)

#         # If the path is not public and user is not authenticated, redirect to login
#         if not is_public_path and not request.user.is_authenticated:
#             return redirect('login')

#         response = self.get_response(request)
#         return response 