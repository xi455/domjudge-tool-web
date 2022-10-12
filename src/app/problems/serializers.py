from app.problems.models import Problem, ProblemInOut
from rest_framework import serializers


class ProblemInOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemInOut
        fields = (
            'input_content',
            'answer_content',
            'is_sample',
        )


class ProblemSerializer(serializers.ModelSerializer):
    int_out_data = ProblemInOutSerializer(many=True)

    class Meta:
        model = Problem
        fields = (
            'id',
            'name',
            'short_name',
            'description_file',
            'time_limit',
            'int_out_data',
            'create_at',
            'update_at',
        )
        read_only_fields = (
            'id',
            'create_at',
            'update_at',
        )
