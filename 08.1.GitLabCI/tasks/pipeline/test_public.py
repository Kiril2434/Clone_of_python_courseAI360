EXPECTED_STAGES = ["lint", "test", "build", "deploy"]
EXPECTED_JOBS = {"lint", "test", "build", "package", "deploy-staging", "deploy-prod"}


def test_yaml_parses(pipeline):
    assert isinstance(pipeline, dict)


def test_has_stages_key(pipeline):
    assert "stages" in pipeline, "Не найден ключ 'stages' на верхнем уровне"


def test_stages_contain_required(pipeline):
    stages = pipeline.get("stages", [])
    for required in EXPECTED_STAGES:
        assert required in stages, f"Stage '{required}' отсутствует"


def test_all_required_jobs_present(jobs):
    missing = EXPECTED_JOBS - set(jobs.keys())
    assert not missing, f"Отсутствуют job'ы: {sorted(missing)}"


def test_each_job_has_stage(jobs):
    for name, cfg in jobs.items():
        assert "stage" in cfg, f"Job '{name}' не имеет ключа 'stage'"


def test_top_level_cache_exists(pipeline):
    assert "cache" in pipeline, "Глобальный cache не настроен"


def test_top_level_variables_exists(pipeline):
    assert "variables" in pipeline, "variables на верхнем уровне не определены"


def test_test_job_has_artifacts(jobs):
    test_job = jobs.get("test", {})
    assert "artifacts" in test_job, "test job не имеет artifacts"


def test_deploy_prod_is_manual(jobs):
    deploy_prod = jobs.get("deploy-prod", {})
    rules = deploy_prod.get("rules", [])
    has_manual = any(
        isinstance(r, dict) and r.get("when") == "manual"
        for r in rules
    ) or deploy_prod.get("when") == "manual"
    assert has_manual, "deploy-prod должен иметь when: manual"
