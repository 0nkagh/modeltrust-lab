import json
from modeltrust.card import build_card_json, build_card_md

def test_card_full_equipment():
    # Tam donanım
    prov = {
        "tool": {"name": "modeltrust", "version": "0.1.0"},
        "environment": {"python": "3.11", "pandas": "2.0", "numpy": "1.24", "platform": "Windows"},
        "run_metadata": {"seed": 42},
        "profile": {"duplicate_rows": {"exact_duplicate_count": 0}},
        "leakage": {
            "checks": [
                {"name": "target_copy_exact", "result": "pass"},
                {"name": "target_copy_near", "result": "pass"},
                {"name": "preprocess.fit_scope", "result": "not_assessable", "reason_code": "requires_pipeline_code"}
            ]
        },
        "split": {
            "modes": {
                "random": {"status": "performed"},
                "group": {"status": "performed"},
                "temporal": {"status": "not_assessable", "reason_code": "time_column_missing"}
            }
        },
        "evaluation": {
            "group_errors": {"status": "performed"},
            "models": [{"name": "ols", "mae": 1.0}],
            "uncertainty": {
                "status": "performed",
                "coverage": 0.91,
                "wilson_low": 0.86,
                "wilson_high": 0.94,
                "nominal": 0.9,
                "mean_width": 3.2
            }
        },
        "shift": {
            "drift": {"feature_ks": {"status": "performed"}},
            "ood": {"feature_range": {"status": "performed"}}
        }
    }
    
    card = build_card_json(prov, "python -m modeltrust card --all")
    
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[5]["status"] == "answered"
    assert q_dict[6]["status"] == "answered"
    assert q_dict[7]["status"] == "answered"
    assert q_dict[8]["status"] == "answered"
    
    assert len(card["metrics"]["models"]) == 1
    assert any(na["check"] == "preprocess.fit_scope" for na in card["not_assessable"])

def test_card_profile_only():
    prov = {
        "profile": {"duplicate_rows": {"exact_duplicate_count": 5}}
    }
    card = build_card_json(prov, "cmd")
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[1]["status"] == "answered"
    assert q_dict[5]["status"] == "not_assessable"
    assert q_dict[6]["status"] == "not_assessable"
    assert q_dict[7]["status"] == "not_assessable"
    assert q_dict[8]["status"] == "not_assessable"

def test_card_q4_rule():
    prov = {
        "split": {
            "modes": {
                "random": {"status": "performed"},
                "group": {"status": "not_assessable"},
                "temporal": {"status": "not_assessable"}
            }
        }
    }
    card = build_card_json(prov, "cmd")
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[4]["status"] == "partial"
    
    prov["split"]["modes"]["group"]["status"] = "performed"
    card = build_card_json(prov, "cmd")
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[4]["status"] == "answered"

def test_card_q9_q10_static():
    card = build_card_json({}, "cmd")
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[9]["status"] == "answered"
    assert q_dict[10]["status"] == "partial"

def test_forbidden_words():
    # 5. Yasaklı dil testi: card.md ve card.json içinde 
    # production-ready, guaranteed, certified, compliant, leakage-proof, fully reliable dizeleri yok.
    card = build_card_json({}, "cmd")
    md = build_card_md(card)
    j = json.dumps(card).lower()
    md = md.lower()
    
    forbidden = ["production-ready", "guaranteed", "certified", "compliant", "leakage-proof", "fully reliable"]
    for w in forbidden:
        assert w not in j
        assert w not in md

def test_scope_fields():
    card = build_card_json({}, "cmd")
    assert card["scope"]["model_loaded"] is False
    assert card["scope"]["external_data_downloaded"] is False
    assert card["scope"]["user_code_executed"] is False

def test_thresholds():
    card = build_card_json({}, "cmd")
    t = card["thresholds"]
    assert "MIN_ROWS_FOR_COPY_CHECK" in t
    # shift and eval thresholds may be missing if imports fail but they should be there
    assert len(t) > 0

def test_determinism():
    prov = {"profile": {"duplicate_rows": {"exact_duplicate_count": 1}}}
    card1 = build_card_json(prov, "cmd")
    card2 = build_card_json(prov, "cmd")
    assert json.dumps(card1, sort_keys=True) == json.dumps(card2, sort_keys=True)

def test_not_assessable_logic():
    prov = {
        "leakage": {
            "checks": [
                {"name": "c1", "result": "not_assessable", "reason_code": "r1"}
            ]
        }
    }
    card = build_card_json(prov, "cmd")
    na = card["not_assessable"]
    assert len(na) == 1
    assert na[0]["module"] == "leakage"
    assert na[0]["check"] == "c1"
    assert na[0]["reason_code"] == "r1"

def test_interval_coverage_null():
    prov = {
        "evaluation": {
            "uncertainty": {"status": "skipped"}
        }
    }
    card = build_card_json(prov, "cmd")
    assert card["metrics"]["interval_coverage"] is None
    
    prov["evaluation"]["uncertainty"] = {"status": "performed", "coverage": 0.5}
    card = build_card_json(prov, "cmd")
    assert card["metrics"]["interval_coverage"]["coverage"] == 0.5

def test_n_scored_all_rows_label_and_value():
    # Supplied-predictions mode: n_scored should equal total rows (no split applied).
    # The card.md column header must say "all rows provided", not "split".
    # Fixture eval_preds.csv has 30 rows; n_scored expected == 30.
    prov = {
        "evaluation": {
            "models": [{
                "name": "supplied_predictions",
                "status": "performed",
                "n_scored": 30,
                "mae": 1.0,
                "rmse": 1.732051,
                "r2": 0.959956,
                "r2_status": "performed",
            }]
        }
    }
    card = build_card_json(prov, "cmd")
    model_row = card["metrics"]["models"][0]
    assert model_row["n_scored"] == 30

    md = build_card_md(card)
    assert "n_scored (all rows provided)" in md
    assert "n_scored (split)" not in md
