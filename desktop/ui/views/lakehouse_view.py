"""Victory Crest One - Data Lakehouse & Predictive ML View
Distributed Apache Parquet storage catalog, batch ETL pipeline orchestration,
and real-time machine learning inference workbench.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QTextEdit, QGroupBox, QScrollArea, QSplitter,
    QDoubleSpinBox, QSpinBox
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from desktop.ui.components.status_badge import StatusBadge
from shared.enums import LakeDatasetType, PipelineRunStatus, MlModelType, DatasetFormat


class LakehouseView(QWidget):
    """Central Data Lakehouse & Predictive Machine Learning Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_datasets: List[Dict[str, Any]] = []
        self.cached_pipelines: List[Dict[str, Any]] = []
        self.cached_models: List[Dict[str, Any]] = []
        self.cached_metrics: Dict[str, Any] = {}

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # -----------------------------------------------------
        # 1. Executive Header Section
        # -----------------------------------------------------
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Data Lakehouse & Predictive ML")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Distributed Apache Parquet columnar storage, ETL pipeline orchestration, and real-time predictive ML inferencing.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_predict = QPushButton("🔮 Run ML Predictor")
        btn_predict.setProperty("class", "btn_secondary")
        btn_predict.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))

        btn_new_ds = QPushButton("➕ Register Dataset")
        btn_new_ds.setProperty("class", "btn_primary")
        btn_new_ds.clicked.connect(self.open_register_dataset_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_predict)
        header_row.addWidget(btn_new_ds)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive KPI Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_storage = self.create_metric_card("LAKE STORAGE / RATIO", "0.00 MB", "Compression Ratio: 1.0x", "#8B5CF6")
        self.card_datasets = self.create_metric_card("PARQUET DATASETS", "0", "Columnar Snappy Partitions", "#10B981")
        self.card_throughput = self.create_metric_card("DAILY PIPELINE VOLUME", "0 recs", "100.0% Success Rate", "#3B82F6")
        self.card_ml_acc = self.create_metric_card("PREDICTIVE ML ACCURACY", "0.0%", "0 Models Deployed", "#F59E0B")

        cards_row.addWidget(self.card_storage)
        cards_row.addWidget(self.card_datasets)
        cards_row.addWidget(self.card_throughput)
        cards_row.addWidget(self.card_ml_acc)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main Lakehouse Tabs
        # -----------------------------------------------------
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                background: {ThemeColors.BG_CARD};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {ThemeColors.BG_CARD};
                color: {ThemeColors.TEXT_MUTED};
                padding: 10px 18px;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {ThemeColors.TEXT_MAIN};
                border-bottom: 2px solid {ThemeColors.PRIMARY};
            }}
            QTabBar::tab:hover {{
                color: {ThemeColors.TEXT_MAIN};
            }}
        """)

        # Tab 1: Parquet Datasets Catalog
        self.tab_datasets = QWidget()
        self.setup_datasets_tab()
        self.tab_widget.addTab(self.tab_datasets, "📦 Columnar Parquet Datasets")

        # Tab 2: ETL Pipelines & Compaction Jobs
        self.tab_pipelines = QWidget()
        self.setup_pipelines_tab()
        self.tab_widget.addTab(self.tab_pipelines, "⚙️ ETL Pipelines & Compactor Jobs")

        # Tab 3: Predictive ML Workbench & Inference Playground
        self.tab_ml = QWidget()
        self.setup_ml_tab()
        self.tab_widget.addTab(self.tab_ml, "🔮 Predictive ML Workbench")

        main_layout.addWidget(self.tab_widget)

    def create_metric_card(self, title: str, value: str, subtext: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 14px 16px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 0.5px;")

        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {accent_color};")

        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        return card

    # =========================================================================
    # TAB 1: COLUMNAR PARQUET DATASETS
    # =========================================================================

    def setup_datasets_tab(self):
        layout = QVBoxLayout(self.tab_datasets)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_type = QLabel("Dataset Domain:")
        lbl_type.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_ds_type = QComboBox()
        self.combo_ds_type.addItems([
            "ALL DOMAINS",
            "FINANCIAL_LEDGER",
            "GUEST_FOLIOS",
            "IOT_SENSOR_STREAM",
            "POS_COMMERCE_TRANSACTIONS"
        ])
        self.combo_ds_type.currentIndexChanged.connect(self.apply_dataset_filters)

        self.txt_ds_search = QLineEdit()
        self.txt_ds_search.setPlaceholderText("🔍 Search dataset by code, name, or partition key...")
        self.txt_ds_search.textChanged.connect(self.apply_dataset_filters)

        filter_row.addWidget(lbl_type)
        filter_row.addWidget(self.combo_ds_type)
        filter_row.addWidget(self.txt_ds_search)
        layout.addLayout(filter_row)

        # Datasets Table
        self.table_datasets = QTableWidget()
        self.table_datasets.setColumnCount(8)
        self.table_datasets.setHorizontalHeaderLabels([
            "Dataset Code", "Dataset Name", "Domain Type", "Format / Codec",
            "Partition Scheme", "Total Records", "Parquet Size", "Compression Ratio"
        ])
        self.table_datasets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_datasets.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_datasets.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_datasets.verticalHeader().setVisible(False)
        self.table_datasets.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_datasets.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_datasets.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_INPUT};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-bottom: 1px solid {ThemeColors.BORDER_DEFAULT};
            }}
        """)
        layout.addWidget(self.table_datasets)

    def populate_datasets_table(self, datasets: List[Dict[str, Any]]):
        self.table_datasets.setRowCount(len(datasets))
        for row, ds in enumerate(datasets):
            # 0: Code
            self.table_datasets.setItem(row, 0, QTableWidgetItem(ds.get("dataset_code", "")))

            # 1: Name
            self.table_datasets.setItem(row, 1, QTableWidgetItem(ds.get("name", "")))

            # 2: Type
            d_type = ds.get("dataset_type", "").replace("_", " ").title()
            self.table_datasets.setItem(row, 2, QTableWidgetItem(d_type))

            # 3: Format / Codec
            fmt = ds.get("format", "PARQUET")
            codec = ds.get("compression_codec", "SNAPPY")
            self.table_datasets.setItem(row, 3, QTableWidgetItem(f"{fmt} ({codec})"))

            # 4: Partition Key
            self.table_datasets.setItem(row, 4, QTableWidgetItem(ds.get("partition_key", "")))

            # 5: Records
            recs = ds.get("record_count", 0)
            self.table_datasets.setItem(row, 5, QTableWidgetItem(f"{recs:,}"))

            # 6: Size
            size_b = float(ds.get("size_bytes", 0))
            size_mb = round(size_b / 1048576.0, 2)
            self.table_datasets.setItem(row, 6, QTableWidgetItem(f"{size_mb} MB"))

            # 7: Ratio
            ratio = ds.get("compression_ratio", "1.00")
            ratio_item = QTableWidgetItem(f"{ratio}x Space Savings")
            ratio_item.setForeground(Qt.green)
            self.table_datasets.setItem(row, 7, ratio_item)

    def apply_dataset_filters(self):
        f_type = self.combo_ds_type.currentText()
        query = self.txt_ds_search.text().lower().strip()

        filtered = []
        for ds in self.cached_datasets:
            if f_type != "ALL DOMAINS" and ds.get("dataset_type", "").upper() != f_type.upper():
                continue
            if query:
                haystack = f"{ds.get('dataset_code', '')} {ds.get('name', '')} {ds.get('partition_key', '')}".lower()
                if query not in haystack:
                    continue
            filtered.append(ds)

        self.populate_datasets_table(filtered)

    # =========================================================================
    # TAB 2: ETL PIPELINES & BATCH COMPACTOR JOBS
    # =========================================================================

    def setup_pipelines_tab(self):
        layout = QVBoxLayout(self.tab_pipelines)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl_desc = QLabel("Lakehouse ETL Ingestion, Partition Compaction, and Micro-Batch Schedulers")
        lbl_desc.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(lbl_desc)

        self.table_pipelines = QTableWidget()
        self.table_pipelines.setColumnCount(8)
        self.table_pipelines.setHorizontalHeaderLabels([
            "Pipeline Code", "Pipeline Title", "Source Module", "Destination Dataset",
            "Schedule", "Status", "Processed Records", "Manual Trigger"
        ])
        self.table_pipelines.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_pipelines.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_pipelines.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_pipelines.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table_pipelines.verticalHeader().setVisible(False)
        self.table_pipelines.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_pipelines.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_pipelines.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_INPUT};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-bottom: 1px solid {ThemeColors.BORDER_DEFAULT};
            }}
        """)
        layout.addWidget(self.table_pipelines)

    def populate_pipelines_table(self, pipelines: List[Dict[str, Any]]):
        self.table_pipelines.setRowCount(len(pipelines))
        for row, p in enumerate(pipelines):
            # 0: Code
            self.table_pipelines.setItem(row, 0, QTableWidgetItem(p.get("pipeline_code", "")))

            # 1: Name
            self.table_pipelines.setItem(row, 1, QTableWidgetItem(p.get("name", "")))

            # 2: Source
            src = p.get("source_module", "").title()
            self.table_pipelines.setItem(row, 2, QTableWidgetItem(src))

            # 3: Target
            self.table_pipelines.setItem(row, 3, QTableWidgetItem(p.get("target_dataset_code", "")))

            # 4: Cron
            self.table_pipelines.setItem(row, 4, QTableWidgetItem(p.get("schedule_cron", "")))

            # 5: Status Badge
            st = p.get("status", "IDLE").upper()
            badge = StatusBadge(st)
            cell_widget = QWidget()
            b_layout = QHBoxLayout(cell_widget)
            b_layout.setContentsMargins(4, 2, 4, 2)
            b_layout.setAlignment(Qt.AlignCenter)
            b_layout.addWidget(badge)
            self.table_pipelines.setCellWidget(row, 5, cell_widget)

            # 6: Records Processed
            recs = p.get("records_processed", 0)
            self.table_pipelines.setItem(row, 6, QTableWidgetItem(f"{recs:,} records"))

            # 7: Trigger button
            btn_run = QPushButton("⚡ Execute")
            btn_run.setStyleSheet(f"font-size: 11px; padding: 3px 8px; background: {ThemeColors.BG_INPUT}; color: {ThemeColors.TEXT_MAIN}; border: 1px solid {ThemeColors.BORDER_DEFAULT}; border-radius: 4px;")
            btn_run.clicked.connect(lambda checked=False, p_id=p["id"]: self.trigger_pipeline_run(p_id))
            self.table_pipelines.setCellWidget(row, 7, btn_run)

    def trigger_pipeline_run(self, pipeline_id: str):
        try:
            res = api_client.run_data_pipeline(pipeline_id)
            recs = res.get("records_processed", 0)
            dur = res.get("duration_seconds", "0.0")
            QMessageBox.information(
                self,
                "Pipeline Execution Complete",
                f"Successfully completed batch extraction & compaction!\nProcessed: {recs:,} records\nDuration: {dur}s"
            )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Pipeline Error", f"Failed to execute pipeline: {str(e)}")

    # =========================================================================
    # TAB 3: PREDICTIVE ML WORKBENCH & INFERENCE PLAYGROUND
    # =========================================================================

    def setup_ml_tab(self):
        layout = QHBoxLayout(self.tab_ml)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Model Registry Table
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        lbl_models = QLabel("Deployed Enterprise Machine Learning Model Registry")
        lbl_models.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {ThemeColors.TEXT_MAIN};")
        left_layout.addWidget(lbl_models)

        self.table_models = QTableWidget()
        self.table_models.setColumnCount(7)
        self.table_models.setHorizontalHeaderLabels([
            "Model Code", "Model Name", "Model Type", "Algorithm",
            "Version", "Accuracy", "Feature Drift"
        ])
        self.table_models.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_models.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_models.verticalHeader().setVisible(False)
        self.table_models.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_models.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_models.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_INPUT};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-bottom: 1px solid {ThemeColors.BORDER_DEFAULT};
            }}
        """)
        left_layout.addWidget(self.table_models)
        splitter.addWidget(left_box)

        # Right Column: Real-Time Inference Playground
        right_box = QFrame()
        right_box.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_INPUT};
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        right_layout = QVBoxLayout(right_box)
        right_layout.setSpacing(12)

        lbl_infer_title = QLabel("🔮 Real-Time ML Inference Tester")
        lbl_infer_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        lbl_infer_desc = QLabel("Select a deployed model and supply scenario inputs to generate demand predictions or churn risk scores.")
        lbl_infer_desc.setWordWrap(True)
        lbl_infer_desc.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED};")

        right_layout.addWidget(lbl_infer_title)
        right_layout.addWidget(lbl_infer_desc)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_ml_model = QComboBox()
        self.combo_ml_model.currentIndexChanged.connect(self.on_model_selection_changed)

        # Feature Inputs
        self.spin_base_demand = QDoubleSpinBox()
        self.spin_base_demand.setRange(0.0, 100.0)
        self.spin_base_demand.setValue(75.0)

        self.spin_seasonality = QDoubleSpinBox()
        self.spin_seasonality.setRange(0.5, 2.0)
        self.spin_seasonality.setValue(1.15)
        self.spin_seasonality.setSingleStep(0.05)

        self.spin_event_mult = QDoubleSpinBox()
        self.spin_event_mult.setRange(0.5, 3.0)
        self.spin_event_mult.setValue(1.05)
        self.spin_event_mult.setSingleStep(0.05)

        self.spin_base_rate = QDoubleSpinBox()
        self.spin_base_rate.setRange(1000.0, 50000.0)
        self.spin_base_rate.setValue(6000.0)

        form.addRow("Select ML Model:", self.combo_ml_model)
        form.addRow("Base Demand (%):", self.spin_base_demand)
        form.addRow("Seasonality Factor:", self.spin_seasonality)
        form.addRow("Special Event Factor:", self.spin_event_mult)
        form.addRow("Baseline Room Rate (₹):", self.spin_base_rate)

        right_layout.addLayout(form)

        btn_run_infer = QPushButton("⚡ Execute Predictive Inference")
        btn_run_infer.setProperty("class", "btn_primary")
        btn_run_infer.clicked.connect(self.trigger_ml_inference)
        right_layout.addWidget(btn_run_infer)

        lbl_pred_res = QLabel("Model Inference Output:")
        lbl_pred_res.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ThemeColors.TEXT_MUTED}; margin-top: 10px;")
        right_layout.addWidget(lbl_pred_res)

        self.txt_infer_output = QTextEdit()
        self.txt_infer_output.setReadOnly(True)
        self.txt_infer_output.setPlaceholderText("Prediction confidence intervals, dynamic pricing tiers, or churn risk probabilities will appear here...")
        self.txt_infer_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-family: monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        right_layout.addWidget(self.txt_infer_output)
        right_layout.addStretch()

        splitter.addWidget(right_box)
        splitter.setSizes([580, 380])
        layout.addWidget(splitter)

    def populate_models_table(self, models: List[Dict[str, Any]]):
        self.table_models.setRowCount(len(models))
        for row, m in enumerate(models):
            # 0: Code
            self.table_models.setItem(row, 0, QTableWidgetItem(m.get("model_code", "")))

            # 1: Name
            self.table_models.setItem(row, 1, QTableWidgetItem(m.get("name", "")))

            # 2: Type
            m_type = m.get("model_type", "").replace("_", " ").title()
            self.table_models.setItem(row, 2, QTableWidgetItem(m_type))

            # 3: Algorithm
            self.table_models.setItem(row, 3, QTableWidgetItem(m.get("algorithm", "")))

            # 4: Version
            self.table_models.setItem(row, 4, QTableWidgetItem(m.get("version", "")))

            # 5: Accuracy
            acc = float(m.get("accuracy_score", 0)) * 100.0
            acc_item = QTableWidgetItem(f"{acc:.2f}%")
            acc_item.setForeground(Qt.green)
            self.table_models.setItem(row, 5, acc_item)

            # 6: Drift
            drift = m.get("feature_drift_percent", "0.0")
            self.table_models.setItem(row, 6, QTableWidgetItem(f"{drift}%"))

    def on_model_selection_changed(self):
        m_code = self.combo_ml_model.currentText()
        if "CHURN" in m_code:
            self.spin_base_demand.setValue(60.0)  # Inactivity days
            self.spin_seasonality.setValue(1.00)
            self.spin_event_mult.setValue(1.00)
        else:
            self.spin_base_demand.setValue(75.0)
            self.spin_seasonality.setValue(1.15)
            self.spin_event_mult.setValue(1.05)

    def trigger_ml_inference(self):
        m_code = self.combo_ml_model.currentText()
        if not m_code:
            return

        if "CHURN" in m_code:
            features = {
                "days_since_last_stay": int(self.spin_base_demand.value()),
                "total_bookings": 3,
                "nps_rating": 8
            }
        else:
            features = {
                "base_demand": float(self.spin_base_demand.value()),
                "seasonality_factor": float(self.spin_seasonality.value()),
                "event_multiplier": float(self.spin_event_mult.value()),
                "base_rate": float(self.spin_base_rate.value())
            }

        try:
            res = api_client.run_ml_inference(m_code, features)
            formatted = json.dumps(res, default=str, indent=2)
            self.txt_infer_output.setPlainText(formatted)
        except Exception as e:
            self.txt_infer_output.setPlainText(f"❌ Inference Error:\n{str(e)}")

    # =========================================================================
    # MODAL DIALOGS
    # =========================================================================

    def open_register_dataset_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New Parquet Dataset")
        dialog.setMinimumWidth(440)
        dialog.setStyleSheet(f"background-color: {ThemeColors.BG_CARD}; color: {ThemeColors.TEXT_MAIN};")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        txt_code = QLineEdit()
        txt_code.setPlaceholderText("e.g. DS-INVENTORY-MOVEMENTS")

        txt_name = QLineEdit()
        txt_name.setPlaceholderText("e.g. Warehouse Inventory Stock Movements Columnar Lake")

        combo_type = QComboBox()
        combo_type.addItems([
            "FINANCIAL_LEDGER",
            "GUEST_FOLIOS",
            "INVENTORY_TELEMETRY",
            "IOT_SENSOR_STREAM",
            "POS_COMMERCE_TRANSACTIONS"
        ])

        txt_partition = QLineEdit("year=YYYY/month=MM")
        txt_uri = QLineEdit("s3://victory-lakehouse/gold/inventory_movements/")

        form.addRow("Dataset Code *:", txt_code)
        form.addRow("Dataset Name *:", txt_name)
        form.addRow("Domain Classification *:", combo_type)
        form.addRow("Partition Scheme *:", txt_partition)
        form.addRow("Storage URI *:", txt_uri)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("Register Dataset")
        btn_save.setProperty("class", "btn_primary")

        def on_save():
            code = txt_code.text().strip().upper()
            name = txt_name.text().strip()
            part = txt_partition.text().strip()
            uri = txt_uri.text().strip()

            if not code or not name or not part or not uri:
                QMessageBox.warning(dialog, "Validation Error", "All fields are required.")
                return

            prop_id = session_manager.active_property.get("id") if session_manager.active_property else None
            payload = {
                "dataset_code": code,
                "name": name,
                "dataset_type": combo_type.currentText(),
                "format": "PARQUET",
                "partition_key": part,
                "compression_codec": "SNAPPY",
                "storage_uri": uri,
                "property_id": prop_id
            }

            try:
                api_client.create_lake_dataset(payload)
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to register dataset: {str(e)}")

        btn_save.clicked.connect(on_save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    # =========================================================================
    # DATA REFRESH
    # =========================================================================

    def refresh_data(self):
        prop_id = session_manager.active_property.get("id") if session_manager.active_property else None

        # Fetch datasets
        try:
            self.cached_datasets = api_client.get_lake_datasets(property_id=prop_id)
        except Exception:
            self.cached_datasets = []

        # Fetch pipelines
        try:
            self.cached_pipelines = api_client.get_data_pipelines(property_id=prop_id)
        except Exception:
            self.cached_pipelines = []

        # Fetch models
        try:
            self.cached_models = api_client.get_ml_models()
        except Exception:
            self.cached_models = []

        # Fetch metrics
        try:
            self.cached_metrics = api_client.get_lakehouse_metrics(property_id=prop_id)
        except Exception:
            self.cached_metrics = {}

        # Update metric cards
        parq_mb = self.cached_metrics.get("total_parquet_size_mb", "0.00")
        ratio = self.cached_metrics.get("overall_compression_ratio", "1.00")
        raw_mb = self.cached_metrics.get("total_raw_size_mb", "0.00")
        tot_ds = self.cached_metrics.get("total_datasets", len(self.cached_datasets))
        recs = self.cached_metrics.get("daily_records_ingested", 0)
        succ_rate = self.cached_metrics.get("pipeline_success_rate_percent", "100.00")
        avg_acc = self.cached_metrics.get("avg_model_accuracy_percent", "0.0")
        tot_mod = self.cached_metrics.get("deployed_ml_models_count", len(self.cached_models))

        self.update_card_labels(self.card_storage, f"{parq_mb} MB ({ratio}x)", f"Uncompressed Raw: {raw_mb} MB")
        self.update_card_labels(self.card_datasets, str(tot_ds), "Columnar Snappy Partitions")
        self.update_card_labels(self.card_throughput, f"{recs:,} recs", f"Pipeline Success: {succ_rate}%")
        self.update_card_labels(self.card_ml_acc, f"{avg_acc}%", f"{tot_mod} ML Models Deployed")

        # Update model combo
        current_sel = self.combo_ml_model.currentText()
        self.combo_ml_model.clear()
        for m in self.cached_models:
            self.combo_ml_model.addItem(m.get("model_code", ""))
        if current_sel:
            idx = self.combo_ml_model.findText(current_sel)
            if idx >= 0:
                self.combo_ml_model.setCurrentIndex(idx)

        # Populate tables
        self.apply_dataset_filters()
        self.populate_pipelines_table(self.cached_pipelines)
        self.populate_models_table(self.cached_models)

    def update_card_labels(self, card: QFrame, val: str, sub: str):
        layout = card.layout()
        if layout and layout.count() >= 3:
            lbl_val = layout.itemAt(1).widget()
            lbl_sub = layout.itemAt(2).widget()
            if isinstance(lbl_val, QLabel):
                lbl_val.setText(val)
            if isinstance(lbl_sub, QLabel):
                lbl_sub.setText(sub)
