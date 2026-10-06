from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Prescription
from .serializers import PrescriptionSerializer, PrescriptionCreateSerializer, VerifyPrescriptionSerializer
from users.permissions import IsPharmacistOrAdmin

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all().select_related('customer', 'verified_by', 'dispensed_by').prefetch_related('items__medicine')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['prescription_number', 'doctor_name', 'customer__name']
    ordering_fields = ['created_at', 'status']

    def get_permissions(self):
        if self.action in ['verify', 'dispense', 'destroy']:
            return [IsPharmacistOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionCreateSerializer
        return PrescriptionSerializer

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        prescription = self.get_object()
        serializer = VerifyPrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verdict = serializer.validated_data['action']
        if verdict == 'APPROVE':
            prescription.status = Prescription.Status.APPROVED
            prescription.verified_by = request.user
            prescription.rejection_reason = None
        elif verdict == 'UNDER_REVIEW':
            prescription.status = Prescription.Status.UNDER_REVIEW
            prescription.verified_by = request.user
        elif verdict == 'REJECT':
            prescription.status = Prescription.Status.REJECTED
            prescription.verified_by = request.user
            prescription.rejection_reason = serializer.validated_data.get('rejection_reason', 'Not specified')

        prescription.save()
        return Response(PrescriptionSerializer(prescription).data)

    @action(detail=True, methods=['post'], url_path='dispense')
    def dispense(self, request, pk=None):
        prescription = self.get_object()
        prescription.status = Prescription.Status.DISPENSED
        prescription.dispensed_by = request.user
        prescription.save()
        return Response(PrescriptionSerializer(prescription).data)
