#ifndef TELEMETRY_MODEL_H
#define TELEMETRY_MODEL_H

#include <QAbstractListModel>
#include <vector>
#include <gnuradio/techniquemaker/interdictor_cpp.h>

class TelemetryModel : public QAbstractListModel {
    Q_OBJECT
public:
    explicit TelemetryModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;

public slots:
    void updateTargets(const std::vector<gr::techniquemaker::interdictor_cpp::Target>& targets);

private:
    std::vector<gr::techniquemaker::interdictor_cpp::Target> d_targets;
};

#endif // TELEMETRY_MODEL_H
