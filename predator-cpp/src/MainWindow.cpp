#include "MainWindow.hpp"
#include "WaveformEngine.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGroupBox>
#include <QFormLayout>
#include <QApplication>
#include <QComboBox>
#include <QCheckBox>
#include <QRadioButton>
#include <QInputDialog>

MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent), 
    d_controller(new InterdictionController(this)),
    d_telemetry_model(new TelemetryModel(this)) {
    d_techniques = WaveformEngine::getTechniques();
    setupUi();
    connect(d_controller, &InterdictionController::targetsUpdated, d_telemetry_model, &TelemetryModel::updateTargets);
    onTemplateChanged(d_template_combo->currentText());
}

MainWindow::~MainWindow() {}

void MainWindow::setupUi() {
    setWindowTitle("Predator-Native [OFFLINE]");
    resize(1400, 900);

    QWidget *central = new QWidget(this);
    setCentralWidget(central);
    QVBoxLayout *main_layout = new QVBoxLayout(central);

    // --- Header ---
    QHBoxLayout *header = new QHBoxLayout();
    QGroupBox *tuning_box = new QGroupBox("Radio Master Control");
    QHBoxLayout *tuning_layout = new QHBoxLayout(tuning_box);
    
    tuning_layout->addWidget(new QLabel("Center Freq:"));
    d_freq_input = new QLineEdit("915000000");
    tuning_layout->addWidget(d_freq_input);
    
    tuning_layout->addWidget(new QLabel("Sample Rate:"));
    d_samp_input = new QLineEdit("2000000");
    tuning_layout->addWidget(d_samp_input);
    
    QPushButton *apply_btn = new QPushButton("APPLY");
    tuning_layout->addWidget(apply_btn);
    header->addWidget(tuning_box, 3);

    d_status_badge = new QLabel("OFFLINE");
    d_status_badge->setFixedWidth(200);
    d_status_badge->setAlignment(Qt::AlignCenter);
    d_status_badge->setStyleSheet("font-size: 18px; font-weight: bold; background: #222; color: #555;");
    header->addWidget(d_status_badge);
    main_layout->addLayout(header);

    // --- Middle Split ---
    QHBoxLayout *middle_layout = new QHBoxLayout();
    main_layout->addLayout(middle_layout);

    // Sidebar
    QTabWidget *tabs = new QTabWidget();
    tabs->setFixedWidth(380);
    middle_layout->addWidget(tabs);

    // Tab 1: Hardware
    QWidget *hw_tab = new QWidget();
    QVBoxLayout *hw_layout = new QVBoxLayout(hw_tab);
    QGroupBox *dev_box = new QGroupBox("Device Setup");
    QFormLayout *dev_layout = new QFormLayout(dev_box);
    
    d_serial_combo = new QComboBox();
    d_serial_combo->setEditable(true);
    d_serial_combo->addItem("34573DD");
    dev_layout->addRow("Serial:", d_serial_combo);

    d_scan_btn = new QPushButton("SCAN");
    d_connect_btn = new QPushButton("CONNECT");
    d_connect_btn->setCheckable(true);
    
    QHBoxLayout *dev_btn_layout = new QHBoxLayout();
    dev_btn_layout->addWidget(d_scan_btn);
    dev_btn_layout->addWidget(d_connect_btn);
    dev_layout->addRow(dev_btn_layout);

    hw_layout->addWidget(dev_box);

    QGroupBox *preset_box = new QGroupBox("Preset Management");
    QFormLayout *preset_layout = new QFormLayout(preset_box);
    d_preset_combo = new QComboBox();
    preset_layout->addRow("Saved Presets:", d_preset_combo);
    
    QPushButton *load_btn = new QPushButton("LOAD PRESET");
    QPushButton *save_btn = new QPushButton("SAVE CURRENT");
    QHBoxLayout *preset_btn_layout = new QHBoxLayout();
    preset_btn_layout->addWidget(load_btn);
    preset_btn_layout->addWidget(save_btn);
    preset_layout->addRow(preset_btn_layout);
    hw_layout->addWidget(preset_box);

    QGroupBox *rf_box = new QGroupBox("Gain & RF Output");
    QFormLayout *rf_layout = new QFormLayout(rf_box);
    d_rx_gain_slider = new QSlider(Qt::Horizontal); d_rx_gain_slider->setRange(0, 76);
    d_tx_gain_slider = new QSlider(Qt::Horizontal); d_tx_gain_slider->setRange(0, 89);
    rf_layout->addRow("RX Gain", d_rx_gain_slider);
    rf_layout->addRow("TX Gain", d_tx_gain_slider);
    d_fire_btn = new QPushButton("DISABLE TRANSMIT");
    d_fire_btn->setCheckable(true);
    rf_layout->addRow(d_fire_btn);
    hw_layout->addWidget(rf_box);
    hw_layout->addStretch();
    tabs->addTab(hw_tab, "Hardware");

    // Tab 2: Interdiction
    QWidget *int_tab = new QWidget();
    QVBoxLayout *int_layout = new QVBoxLayout(int_tab);
    QGroupBox *template_box = new QGroupBox("Warhead Selection");
    QVBoxLayout *template_layout = new QVBoxLayout(template_box);
    
    d_template_combo = new QComboBox();
    for (const auto& t : d_techniques) {
        d_template_combo->addItem(QString::fromStdString(t.name));
    }
    template_layout->addWidget(d_template_combo);

    QGroupBox *hydra_box = new QGroupBox("Hydra Auto-Surgical Engine");
    QFormLayout *hydra_layout = new QFormLayout(hydra_box);
    d_hydra_cb = new QCheckBox("Enable Autonomous Comb");
    hydra_layout->addRow(d_hydra_cb);

    d_sabotage_cb = new QCheckBox("Preamble Sabotage (Timing Attack)");
    hydra_layout->addRow(d_sabotage_cb);

    d_sabotage_input = new QLineEdit("20.0");
    hydra_layout->addRow("Sabotage Duration (ms):", d_sabotage_input);
    
    d_targets_label = new QLabel("Max Targets: 1");
    d_targets_slider = new QSlider(Qt::Horizontal);
    d_targets_slider->setRange(1, 50);
    hydra_layout->addRow(d_targets_label, d_targets_slider);

    d_thresh_label = new QLabel("Threshold: -45 dB");
    d_thresh_slider = new QSlider(Qt::Horizontal);
    d_thresh_slider->setRange(-120, 0);
    d_thresh_slider->setValue(-45);
    hydra_layout->addRow(d_thresh_label, d_thresh_slider);
    
    int_layout->addWidget(hydra_box);

    QGroupBox *sticky_box = new QGroupBox("Sticky Channel Denial & Gating");
    QFormLayout *sticky_layout = new QFormLayout(sticky_box);
    d_sticky_cb = new QCheckBox("Enable Persistent Trap");
    sticky_layout->addRow(d_sticky_cb);

    d_predictive_cb = new QCheckBox("Enable Predictive Tracking (PRNG Cracker)");
    sticky_layout->addRow(d_predictive_cb);
    
    d_look_input = new QLineEdit("10.0");
    sticky_layout->addRow("Look-thru (ms):", d_look_input);
    
    d_cycle_input = new QLineEdit("90.0");
    sticky_layout->addRow("Jam Cycle (ms):", d_cycle_input);
    
    d_flush_btn = new QPushButton("FLUSH DENIAL GRID");
    d_flush_btn->setStyleSheet("background-color: #400; color: white;");
    sticky_layout->addRow(d_flush_btn);
    
    int_layout->addWidget(sticky_box);

    QGroupBox *param_group = new QGroupBox("Technique Parameters");
    d_param_layout = new QFormLayout(param_group);
    template_layout->addWidget(param_group);

    int_layout->addWidget(template_box);
    int_layout->addStretch();
    tabs->addTab(int_tab, "Interdiction");

    // Waterfall (Placeholder until connected)
    QWidget *wf_container = new QWidget();
    wf_container->setStyleSheet("background: black;");
    QVBoxLayout *wf_layout = new QVBoxLayout(wf_container);
    middle_layout->addWidget(wf_container, 5);

    // Track Log
    QVBoxLayout *track_panel = new QVBoxLayout();
    track_panel->addWidget(new QLabel("DYNAMIC TRACK LOG"));
    d_track_log = new QListView();
    d_track_log->setFixedWidth(250);
    d_track_log->setModel(d_telemetry_model);
    d_track_log->setStyleSheet("background-color: #111; color: #0F0; font-family: monospace;");
    track_panel->addWidget(d_track_log);
    middle_layout->addLayout(track_panel);

    // Connections
    connect(d_scan_btn, &QPushButton::clicked, this, &MainWindow::onScanClicked);
    connect(d_connect_btn, &QPushButton::toggled, this, &MainWindow::onConnectClicked);
    connect(d_freq_input, &QLineEdit::returnPressed, this, &MainWindow::onFreqChanged);
    connect(d_tx_gain_slider, &QSlider::valueChanged, this, &MainWindow::onTxGainChanged);
    connect(d_rx_gain_slider, &QSlider::valueChanged, this, &MainWindow::onRxGainChanged);
    connect(d_fire_btn, &QPushButton::toggled, this, &MainWindow::onFireToggled);
    connect(d_template_combo, &QComboBox::currentTextChanged, this, &MainWindow::onTemplateChanged);
    connect(d_hydra_cb, &QCheckBox::toggled, this, &MainWindow::onHydraToggled);
    connect(d_sabotage_cb, &QCheckBox::toggled, this, &MainWindow::onSabotageToggled);
    connect(d_sabotage_input, &QLineEdit::editingFinished, this, &MainWindow::onSabotageDurationChanged);
    connect(d_sticky_cb, &QCheckBox::toggled, this, &MainWindow::onStickyToggled);
    connect(d_predictive_cb, &QCheckBox::toggled, this, &MainWindow::onPredictiveToggled);
    connect(d_look_input, &QLineEdit::editingFinished, this, &MainWindow::onLookThroughChanged);
    connect(d_cycle_input, &QLineEdit::editingFinished, this, &MainWindow::onJamCycleChanged);
    connect(d_flush_btn, &QPushButton::clicked, this, &MainWindow::onFlushTargetsClicked);
    connect(load_btn, &QPushButton::clicked, this, &MainWindow::onLoadPresetClicked);
    connect(save_btn, &QPushButton::clicked, this, &MainWindow::onSavePresetClicked);
    connect(d_targets_slider, &QSlider::valueChanged, this, &MainWindow::onMaxTargetsChanged);
    connect(d_thresh_slider, &QSlider::valueChanged, this, &MainWindow::onThresholdChanged);
    
    loadPresets();
}

void MainWindow::onSavePresetClicked() {
    bool ok;
    QString name = QInputDialog::getText(this, "Save Preset", "Preset Name:", QLineEdit::Normal, "", &ok);
    if (!ok || name.isEmpty()) return;

    QFile file(d_preset_file);
    QJsonObject presets;
    if (file.open(QIODevice::ReadOnly)) {
        presets = QJsonDocument::fromJson(file.readAll()).object();
        file.close();
    }

    QJsonObject current;
    current["freq"] = d_freq_input->text();
    current["samp_rate"] = d_samp_input->text();
    current["warhead"] = d_template_combo->currentText();
    
    QJsonObject params;
    for (auto const& [name, widget] : d_param_widgets) {
        if (auto *le = qobject_cast<QLineEdit*>(widget)) params[QString::fromStdString(name)] = le->text();
        else if (auto *cb = qobject_cast<QComboBox*>(widget)) params[QString::fromStdString(name)] = cb->currentText();
    }
    current["params"] = params;
    current["hydra"] = d_hydra_cb->isChecked();
    current["sticky"] = d_sticky_cb->isChecked();
    
    presets[name] = current;
    if (file.open(QIODevice::WriteOnly)) {
        file.write(QJsonDocument(presets).toJson());
        file.close();
    }
    loadPresets();
    d_preset_combo->setCurrentText(name);
}

void MainWindow::onLoadPresetClicked() {
    QString name = d_preset_combo->currentText();
    if (name.isEmpty()) return;

    QFile file(d_preset_file);
    if (!file.open(QIODevice::ReadOnly)) return;
    QJsonObject presets = QJsonDocument::fromJson(file.readAll()).object();
    file.close();

    if (!presets.contains(name)) return;
    QJsonObject config = presets[name].toObject();

    d_freq_input->setText(config["freq"].toString());
    d_samp_input->setText(config["samp_rate"].toString());
    d_template_combo->setCurrentText(config["warhead"].toString());
    
    // Trigger UI generation
    onTemplateChanged(d_template_combo->currentText());

    QJsonObject params = config["params"].toObject();
    for (auto const& key : params.keys()) {
        std::string s_key = key.toStdString();
        if (d_param_widgets.count(s_key)) {
            QWidget *w = d_param_widgets[s_key];
            if (auto *le = qobject_cast<QLineEdit*>(w)) le->setText(params[key].toString());
            else if (auto *cb = qobject_cast<QComboBox*>(w)) cb->setCurrentText(params[key].toString());
        }
    }

    d_hydra_cb->setChecked(config["hydra"].toBool());
    d_sticky_cb->setChecked(config["sticky"].toBool());
    updateWaveform();
}

void MainWindow::loadPresets() {
    d_preset_combo->clear();
    QFile file(d_preset_file);
    if (file.open(QIODevice::ReadOnly)) {
        QJsonObject presets = QJsonDocument::fromJson(file.readAll()).object();
        for (const auto& key : presets.keys()) d_preset_combo->addItem(key);
        file.close();
    }
}

void MainWindow::onTemplateChanged(const QString& text) {
    clearDynamicParams();

    // Find technique metadata
    std::string tech_name = text.toStdString();
    const WaveformEngine::Technique* selected_tech = nullptr;
    for (const auto& t : d_techniques) {
        if (t.name == tech_name) {
            selected_tech = &t;
            break;
        }
    }

    if (!selected_tech) return;

    // Build UI for each parameter
    for (const auto& p : selected_tech->parameters) {
        if (p.type == "entry") {
            QLineEdit *le = new QLineEdit(QString::fromStdString(p.default_val));
            connect(le, &QLineEdit::editingFinished, this, &MainWindow::updateWaveform);
            d_param_layout->addRow(QString::fromStdString(p.title), le);
            d_param_widgets[p.name] = le;
        } else if (p.type == "options") {
            QComboBox *cb = new QComboBox();
            for (const auto& choice : p.choices) {
                cb->addItem(QString::fromStdString(choice));
            }
            cb->setCurrentText(QString::fromStdString(p.default_val));
            connect(cb, &QComboBox::currentTextChanged, this, &MainWindow::updateWaveform);
            d_param_layout->addRow(QString::fromStdString(p.title), cb);
            d_param_widgets[p.name] = cb;
        }
    }

    updateWaveform();
}

void MainWindow::clearDynamicParams() {
    while (d_param_layout->count() > 0) {
        QLayoutItem *item = d_param_layout->takeAt(0);
        if (item->widget()) {
            item->widget()->deleteLater();
        }
        delete item;
    }
    d_param_widgets.clear();
}

void MainWindow::updateWaveform() {
    QString template_name = d_template_combo->currentText();
    double samp_rate = d_samp_input->text().toDouble();
    
    auto get_val = [&](const std::string& name) -> QString {
        if (d_param_widgets.count(name)) {
            QWidget *w = d_param_widgets[name];
            if (auto *le = qobject_cast<QLineEdit*>(w)) return le->text();
            if (auto *cb = qobject_cast<QComboBox*>(w)) return cb->currentText();
        }
        return "";
    };

    std::vector<std::complex<float>> wf;
    std::string filter = get_val("filter_type").toStdString();
    float target = get_val("target_value").toFloat();
    std::string norm = get_val("normalization_type").toStdString();

    if (template_name == "Narrowband Noise") {
        wf = WaveformEngine::narrowbandNoise(get_val("bandwidth_hz").toDouble(), samp_rate, get_val("technique_length_seconds").toDouble(), get_val("interference_type").toStdString(), target, norm, filter);
    } else if (template_name == "Differential Comb") {
        wf = WaveformEngine::differentialComb(get_val("spike_spacing_hz").toDouble(), get_val("spike_count").toInt(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "RRC Modulated Noise") {
        wf = WaveformEngine::rrcModulatedNoise(get_val("symbol_rate_hz").toDouble(), samp_rate, get_val("rolloff").toDouble(), get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "Swept Noise") {
        wf = WaveformEngine::sweptNoise(get_val("sweep_hz").toDouble(), get_val("bandwidth_hz").toDouble(), samp_rate, get_val("technique_length_seconds").toDouble(), get_val("sweep_type").toStdString(), get_val("sweep_rate_hz_s").toDouble(), get_val("interference_type").toStdString(), target, norm, filter);
    } else if (template_name == "Chunked Noise") {
        wf = WaveformEngine::chunkedNoise(get_val("technique_width_hz").toDouble(), get_val("chunks").toInt(), samp_rate, get_val("technique_length_seconds").toDouble(), get_val("interference_type").toStdString(), target, norm, filter);
    } else if (template_name == "Noise Tones") {
        wf = WaveformEngine::noiseTones(get_val("frequencies_str").toStdString(), get_val("bandwidth_hz").toDouble(), samp_rate, get_val("technique_length_seconds").toDouble(), get_val("interference_type").toStdString(), target, norm, filter);
    } else if (template_name == "Cosine Tones") {
        wf = WaveformEngine::cosineTones(get_val("frequencies_str").toStdString(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "Phasor Tones") {
        wf = WaveformEngine::phasorTones(get_val("frequencies_str").toStdString(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "Swept Phasors") {
        wf = WaveformEngine::sweptPhasors(get_val("sweep_hz").toDouble(), get_val("tones").toInt(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "Swept Cosines") {
        wf = WaveformEngine::sweptCosines(get_val("sweep_hz").toDouble(), get_val("tones").toInt(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "FM Cosine") {
        wf = WaveformEngine::fmCosine(get_val("sweep_range_hz").toDouble(), get_val("modulated_frequency").toDouble(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "LFM Chirp") {
        wf = WaveformEngine::lfmChirp(get_val("start_freq_hz").toDouble(), get_val("end_freq_hz").toDouble(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "FHSS Noise") {
        wf = WaveformEngine::fhssNoise(get_val("hop_frequencies_str").toStdString(), get_val("hop_duration_seconds").toDouble(), get_val("bandwidth_hz").toDouble(), samp_rate, get_val("technique_length_seconds").toDouble(), get_val("interference_type").toStdString(), target, norm, filter);
    } else if (template_name == "OFDM-Shaped Noise") {
        wf = WaveformEngine::ofdmShapedNoise(get_val("fft_size").toInt(), get_val("num_subcarriers").toInt(), get_val("cp_length").toInt(), samp_rate, get_val("technique_length_seconds").toDouble(), target, norm, filter);
    } else if (template_name == "Song Maker") {
        wf = WaveformEngine::songMaker(get_val("songName").toStdString(), get_val("bandwidth_hz").toDouble(), samp_rate, target, norm, filter);
    } else if (template_name == "Correlator Confusion") {
        wf = WaveformEngine::correlatorConfusion(get_val("bandwidth_hz").toDouble(), samp_rate, 0.1, get_val("pulse_interval_ms").toDouble(), get_val("confusion_mode").toStdString(), target, norm, filter);
    }

    d_controller->setBaseWaveform(wf);
}

void MainWindow::onScanClicked() {
    d_serial_combo->clear();
    auto devices = InterdictionController::discoverDevices();
    for (const auto& d : devices) {
        d_serial_combo->addItem(QString::fromStdString(d));
    }
}

void MainWindow::onConnectClicked() {
    if (d_connect_btn->isChecked()) {
        std::string selected = d_serial_combo->currentText().split(" ")[0].toStdString();
        d_controller->setup(selected, d_samp_input->text().toDouble(), d_freq_input->text().toDouble());
        d_controller->start();
        
        // Replace black placeholder with real waterfall
        QWidget* wf_widget = d_controller->getWaterfallWidget();
        if (wf_widget) {
            // Find the waterfall container and add it
            // (Note: In a real app, we'd manage this more cleanly)
        }
        
        d_status_badge->setText("CONNECTED");
        d_status_badge->setStyleSheet("font-size: 18px; font-weight: bold; background: #040; color: #0F0;");
    } else {
        d_controller->stop();
        d_status_badge->setText("OFFLINE");
    }
}

void MainWindow::onFreqChanged() { d_controller->setFreq(d_freq_input->text().toDouble()); }
void MainWindow::onSampRateChanged() { d_controller->setSampleRate(d_samp_input->text().toDouble()); }
void MainWindow::onTxGainChanged(int val) { d_controller->setTxGain(val); }
void MainWindow::onRxGainChanged(int val) { d_controller->setRxGain(val); }
void MainWindow::onFireToggled(bool checked) { d_controller->setJammingEnabled(!checked); }

void MainWindow::onHydraToggled(bool checked) {
    d_controller->setOutputMode(checked ? "Auto-Surgical" : "Continuous (Stream)");
}

void MainWindow::onMaxTargetsChanged(int val) {
    d_targets_label->setText(QString("Max Targets: %1").arg(val));
    d_controller->setMaxTargets(val);
}

void MainWindow::onSabotageToggled(bool checked) {
    d_controller->setPreambleSabotage(checked);
}

void MainWindow::onSabotageDurationChanged() {
    d_controller->setSabotageDuration(d_sabotage_input->text().toDouble());
}

void MainWindow::onStickyToggled(bool checked) {
    d_controller->setStickyDenial(checked);
}

void MainWindow::onPredictiveToggled(bool checked) {
    d_controller->setPredictiveTracking(checked);
}

void MainWindow::onLookThroughChanged() {
    d_controller->setLookThroughMs(d_look_input->text().toDouble());
}

void MainWindow::onJamCycleChanged() {
    d_controller->setJamCycleMs(d_cycle_input->text().toDouble());
}

void MainWindow::onFlushTargetsClicked() {
    d_controller->clearTargets();
}

void MainWindow::onThresholdChanged(int val) {
    d_thresh_label->setText(QString("Threshold: %1 dB").arg(val));
    d_controller->setThreshold(static_cast<double>(val));
}
