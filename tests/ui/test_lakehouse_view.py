"""Victory Crest One - Desktop UI Tests for Data Lakehouse & Predictive ML View
Verifies initialization, metric cards, dataset catalog, pipeline triggers,
ML inference playground, and MainWindow stack navigation at index 20.
"""

import pytest
from desktop.ui.views.lakehouse_view import LakehouseView
from desktop.ui.main_window import MainWindow


def test_lakehouse_view_initialization(qapp):
    view = LakehouseView()
    assert view is not None

    # Check metric cards
    assert view.card_storage is not None
    assert view.card_datasets is not None
    assert view.card_throughput is not None
    assert view.card_ml_acc is not None

    # Check 3 tabs
    assert view.tab_widget.count() == 3

    # Check datasets table
    assert view.table_datasets.rowCount() >= 4

    # Check pipelines table
    assert view.table_pipelines.rowCount() >= 4

    # Check models table
    assert view.table_models.rowCount() >= 3

    # Check inference combo
    assert view.combo_ml_model.count() >= 3


def test_lakehouse_view_ml_inference(qapp):
    view = LakehouseView()

    # Select demand forecaster model and trigger prediction
    view.combo_ml_model.setCurrentText("ML-DEMAND-PROP")
    view.spin_base_demand.setValue(82.0)
    view.trigger_ml_inference()

    output = view.txt_infer_output.toPlainText()
    assert "ML-DEMAND-PROP" in output
    assert "prediction" in output
    assert "predicted_demand_percent" in output


def test_main_window_lakehouse_navigation(qapp):
    window = MainWindow()
    assert "analytics_lake" in window.nav_buttons

    window.navigate_to("analytics_lake")
    assert window.view_stack.currentIndex() == 20
    assert window.current_nav_key == "analytics_lake"
    assert window.lakehouse_view is not None
