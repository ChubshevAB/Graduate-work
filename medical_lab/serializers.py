from rest_framework import serializers
from .models import Patient, Analysis, AnalysisType
from django.contrib.auth import get_user_model

User = get_user_model()


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'last_name', 'first_name', 'middle_name', 'full_name',
            'birth_date', 'age', 'gender', 'phone', 'email', 'address',
            'medical_history', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class AnalysisTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisType
        fields = ['id', 'name', 'description', 'price', 'preparation_instructions',
                 'turnaround_time', 'is_active']


class AnalysisSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    analysis_type_name = serializers.CharField(source='analysis_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lab_technician_username = serializers.CharField(source='lab_technician.username', read_only=True)

    class Meta:
        model = Analysis
        fields = [
            'id', 'patient', 'patient_name', 'analysis_type', 'analysis_type_name',
            'status', 'status_display', 'created_at', 'updated_at',
            'collection_date', 'completion_date', 'result', 'result_values',
            'normal_range', 'notes', 'lab_technician', 'lab_technician_username'
        ]
