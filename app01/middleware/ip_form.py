class VisitLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 获取客户端IP
        client_ip = request.META.get("REMOTE_ADDR", "unknown")
        # 请求方法 GET/POST，访问的路径，打印到控制台
        print(f"【来访】IP:{client_ip} | {request.method} | path:{request.path}")

        response = self.get_response(request)
        return response
