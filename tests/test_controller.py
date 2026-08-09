"""测试业务逻辑控制器。"""

from __future__ import annotations

import pytest

from software_copyright_toolkit.controller import (
    TaskConfig,
    estimate_pages,
    format_success_message,
    validate_task_config,
)


class TestTaskConfig:
    """测试 TaskConfig 数据类。"""

    def test_creation(self, tmp_path):
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path / "out",
            software_name="TestApp",
            version="V1.0",
            separator="===== 文件: {path} =====",
            generate_report=True,
            generate_identification=True,
            generate_full=True,
        )
        assert config.target == tmp_path
        assert config.software_name == "TestApp"
        assert config.generate_report is True

    def test_frozen(self, tmp_path):
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="Test",
            version="V1.0",
            separator="=",
            generate_report=True,
            generate_identification=False,
            generate_full=False,
        )
        with pytest.raises(AttributeError):
            config.software_name = "Changed"  # type: ignore[misc]


class TestValidateTaskConfig:
    """测试配置验证。"""

    def test_valid_config(self, tmp_path):
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="TestApp",
            version="V1.0",
            separator="=",
            generate_report=True,
            generate_identification=False,
            generate_full=False,
        )
        errors = validate_task_config(config)
        assert errors == []

    def test_nonexistent_target(self, tmp_path):
        config = TaskConfig(
            target=tmp_path / "nonexistent",
            output_dir=tmp_path,
            software_name="TestApp",
            version="V1.0",
            separator="=",
            generate_report=True,
            generate_identification=False,
            generate_full=False,
        )
        errors = validate_task_config(config)
        assert len(errors) > 0
        assert "不存在" in errors[0]

    def test_no_selection(self, tmp_path):
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="TestApp",
            version="V1.0",
            separator="=",
            generate_report=False,
            generate_identification=False,
            generate_full=False,
        )
        errors = validate_task_config(config)
        assert len(errors) > 0
        assert "至少选择" in errors[0]

    def test_missing_software_name(self, tmp_path):
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="",
            version="V1.0",
            separator="=",
            generate_report=False,
            generate_identification=True,
            generate_full=False,
        )
        errors = validate_task_config(config)
        assert any("软件名称" in e for e in errors)

    def test_missing_version(self, tmp_path):
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="TestApp",
            version="",
            separator="=",
            generate_report=False,
            generate_identification=True,
            generate_full=False,
        )
        errors = validate_task_config(config)
        assert any("版本号" in e for e in errors)

    def test_report_only_no_name_required(self, tmp_path):
        """仅生成报告时不需要软件名称。"""
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="",
            version="",
            separator="=",
            generate_report=True,
            generate_identification=False,
            generate_full=False,
        )
        errors = validate_task_config(config)
        assert errors == []


class TestEstimatePages:
    """测试页数估算。"""

    def test_small(self):
        assert estimate_pages(100) == 2  # 100 / 50 = 2

    def test_exact_page(self):
        assert estimate_pages(50) == 1

    def test_two_pages(self):
        assert estimate_pages(51) == 2

    def test_large(self):
        assert estimate_pages(3000) == 60

    def test_zero(self):
        assert estimate_pages(0) == 1


class TestFormatSuccessMessage:
    """测试成功消息格式化。"""

    def test_with_report_and_word(self, tmp_path):
        from software_copyright_toolkit.controller import GenerationResult

        result = GenerationResult(
            generated_files=[tmp_path / "report.md", tmp_path / "doc.docx"],
            output_dir=tmp_path,
            stats_count=10,
            skipped_count=2,
            effective_lines=500,
            source_content_lines=400,
            identification_content_lines=300,
            warnings=[],
        )
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="Test",
            version="V1.0",
            separator="=",
            generate_report=True,
            generate_identification=True,
            generate_full=True,
        )
        message = format_success_message(result, config)
        assert "10" in message
        assert "500" in message
        assert "300" in message

    def test_with_warnings(self, tmp_path):
        from software_copyright_toolkit.controller import GenerationResult

        result = GenerationResult(
            generated_files=[tmp_path / "doc.docx"],
            output_dir=tmp_path,
            stats_count=0,
            skipped_count=0,
            effective_lines=0,
            source_content_lines=100,
            identification_content_lines=100,
            warnings=["页数不足"],
        )
        config = TaskConfig(
            target=tmp_path,
            output_dir=tmp_path,
            software_name="Test",
            version="V1.0",
            separator="=",
            generate_report=False,
            generate_identification=True,
            generate_full=False,
        )
        message = format_success_message(result, config)
        assert "页数不足" in message
        assert "警告" in message
