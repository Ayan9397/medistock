from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.views.generic import TemplateView
from .services import get_kpis, get_chart_data

class DashboardKPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        return Response(get_kpis())

class DashboardChartsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        return Response(get_chart_data())

class FrontendAppView(TemplateView):
    template_name = "index.html"
