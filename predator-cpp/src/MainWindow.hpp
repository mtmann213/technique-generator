#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QPushButton>
#include <QLineEdit>
#include <QTabWidget>
#include <QComboBox>
#include <QCheckBox>
#include <QListView>
#include <QLabel>
#include <QSlider>
#include <QFormLayout>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <map>
#include "InterdictionController.hpp"
#include "TelemetryModel.hpp"
#include "WaveformEngine.hpp"

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onConnectClicked();
    void onScanClicked();
    void onFreqChanged();
    void onSampRateChanged();
    void onTxGainChanged(int value);
    void onRxGainChanged(int value);
    void onThresholdChanged(int value);
    void onHydraToggled(bool checked);
    void onMaxTargetsChanged(int value);
    void onSabotageToggled(bool checked);
    void onSabotageDurationChanged();
    void onStickyToggled(bool checked);
    void onPredictiveToggled(bool checked);
    void onLookThroughChanged();
    void onJamCycleChanged();
    void onFlushTargetsClicked();
    void onSavePresetClicked();
    void onLoadPresetClicked();
    void onFireToggled(bool checked);
    void onTemplateChanged(const QString& text);

private:
    void setupUi();
    void updateWaveform();
    void clearDynamicParams();
    void loadPresets();

    InterdictionController *d_controller;
    TelemetryModel *d_telemetry_model;
    std::vector<WaveformEngine::Technique> d_techniques;
    std::map<std::string, QWidget*> d_param_widgets;
    const QString d_preset_file = "config/predator_presets_cpp.json";

    // UI Elements
    QFormLayout *d_param_layout;
    QVBoxLayout *d_wf_layout;
    QComboBox *d_serial_combo;
    QComboBox *d_template_combo;
    QComboBox *d_preset_combo;
    QCheckBox *d_hydra_cb;
    QCheckBox *d_sabotage_cb;
    QCheckBox *d_sticky_cb;
    QCheckBox *d_predictive_cb;
    QLineEdit *d_sabotage_input;
    QLineEdit *d_look_input;
    QLineEdit *d_cycle_input;
    QPushButton *d_flush_btn;
    QSlider *d_targets_slider;
    QLabel *d_targets_label;
    QLabel *d_thresh_label;
    QPushButton *d_scan_btn;
    QLineEdit *d_freq_input;
    QLineEdit *d_samp_input;
    QPushButton *d_connect_btn;
    QPushButton *d_fire_btn;
    QLabel *d_status_badge;
    QSlider *d_tx_gain_slider;
    QSlider *d_rx_gain_slider;
    QSlider *d_thresh_slider;
    QListView *d_track_log;
};

#endif // MAINWINDOW_H
