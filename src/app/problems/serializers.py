from django.db import transaction
from rest_framework import serializers

from app.problems.models import Problem, ProblemInOut


class ProblemInOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemInOut
        fields = (
            "input_content",
            "answer_content",
            "is_sample",
        )


class ProblemSerializer(serializers.ModelSerializer):
    int_out_data = ProblemInOutSerializer(many=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        data["owner"] = self.context["request"].user
        return data

    @transaction.atomic
    def create(self, validated_data):
        int_out_data = validated_data.pop("int_out_data", default=[])
        obj = super().create(validated_data)
        int_out_objs = [ProblemInOut(problem=obj, **item) for item in int_out_data]
        ProblemInOut.objects.bulk_create(int_out_objs)
        return Problem.objects.prefetch_related("int_out_data").get(pk=obj.pk)

    @transaction.atomic
    def update(self, instance, validated_data):
        int_out_data = validated_data.pop("int_out_data", default=[])
        obj = super().update(instance, validated_data)
        if int_out_data:
            obj.int_out_data.all().delete()
            int_out_objs = [ProblemInOut(problem=obj, **item) for item in int_out_data]
            ProblemInOut.objects.bulk_create(int_out_objs)

        return Problem.objects.prefetch_related("int_out_data").get(pk=obj.pk)

    class Meta:
        model = Problem
        fields = (
            "id",
            "name",
            "short_name",
            "description_file",
            "time_limit",
            "int_out_data",
            "create_at",
            "update_at",
        )
        read_only_fields = (
            "id",
            "create_at",
            "update_at",
        )
