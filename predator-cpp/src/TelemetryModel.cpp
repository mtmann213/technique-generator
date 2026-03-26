#include "TelemetryModel.hpp"
#include <cstdio>

TelemetryModel::TelemetryModel(QObject *parent) : QAbstractListModel(parent) {}

int TelemetryModel::rowCount(const QModelIndex &parent) const {
    return static_cast<int>(d_targets.size());
}

QVariant TelemetryModel::data(const QModelIndex &index, int role) const {
    if (!index.isValid() || index.row() >= d_targets.size()) return QVariant();

    if (role == Qt::DisplayRole) {
        const auto& t = d_targets[index.row()];
        char buf[128];
        snprintf(buf, sizeof(buf), "%8.1f kHz | %4.1f k", t.center_freq / 1e3, t.bandwidth / 1e3);
        return QString(buf);
    }
    return QVariant();
}

void TelemetryModel::updateTargets(const std::vector<gr::techniquemaker::interdictor_cpp::Target>& targets) {
    beginResetModel();
    d_targets = targets;
    endResetModel();
}
