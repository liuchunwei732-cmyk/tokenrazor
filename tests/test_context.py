"""项目感知引擎测试。"""

from tokenrazor.context import ProjectContext, detect_project


class TestProjectContext:

    def test_detect_unknown(self, tmp_path):
        """空目录应该返回 unknown。"""
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "unknown"
        assert ctx.framework == "unknown"

    def test_detect_node_project(self, tmp_path):
        """有 package.json 的目录应识别为前端。"""
        pkg = tmp_path / "package.json"
        pkg.write_text('{"name": "test"}')
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "frontend"
        assert ctx.framework == "node"
        assert "package.json" in ctx.features

    def test_detect_vite_react(self, tmp_path):
        """vite.config.ts 应识别为 Vite React 前端。"""
        vite = tmp_path / "vite.config.ts"
        vite.write_text("export default {}")
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "frontend"
        assert ctx.framework == "vite_react"

    def test_detect_maven(self, tmp_path):
        """pom.xml 应识别为 Spring Boot 后端。"""
        pom = tmp_path / "pom.xml"
        pom.write_text("<project></project>")
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "backend"
        assert ctx.framework == "springboot"

    def test_detect_gradle(self, tmp_path):
        """build.gradle 应识别为 Gradle 后端。"""
        build = tmp_path / "build.gradle"
        build.write_text("dependencies {}")
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "backend"
        assert ctx.build_tool == "gradle"

    def test_detect_flutter(self, tmp_path):
        """pubspec.yaml 应识别为 Flutter 移动端。"""
        pub = tmp_path / "pubspec.yaml"
        pub.write_text("name: test")
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "mobile"
        assert ctx.framework == "flutter"

    def test_detect_go(self, tmp_path):
        """go.mod 应识别为 Go 后端。"""
        go = tmp_path / "go.mod"
        go.write_text("module test")
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "backend"
        assert ctx.language == "go"

    def test_recommended_ignores_frontend(self, tmp_path):
        """前端项目应有合理的忽略规则。"""
        pkg = tmp_path / "package.json"
        pkg.write_text("{}")
        ctx = detect_project(str(tmp_path))
        assert "node_modules" in ctx.recommended_ignores
        assert "dist" in ctx.recommended_ignores
        assert "build" in ctx.recommended_ignores

    def test_recommended_folds_frontend(self, tmp_path):
        """前端项目应推荐折叠 node_modules。"""
        pkg = tmp_path / "package.json"
        pkg.write_text("{}")
        ctx = detect_project(str(tmp_path))
        assert "node_modules" in ctx.recommended_folds

    def test_generate_snapshot(self, tmp_path):
        """快照应包含项目类型信息。"""
        pkg = tmp_path / "package.json"
        pkg.write_text("{}")
        ctx = detect_project(str(tmp_path))
        snapshot = ctx.generate_snapshot()
        assert "frontend" in snapshot
        assert "目录结构" in snapshot

    def test_dockerfile_detection(self, tmp_path):
        """Dockerfile 应识别为运维项目。"""
        docker = tmp_path / "Dockerfile"
        docker.write_text("FROM ubuntu")
        ctx = detect_project(str(tmp_path))
        assert ctx.project_type == "devops"
