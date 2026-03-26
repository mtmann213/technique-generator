#include <QApplication>
#include "MainWindow.hpp"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    
    // Set global style for a dark "tactical" look
    app.setStyle("Fusion");
    
    MainWindow win;
    win.show();
    
    return app.exec();
}
