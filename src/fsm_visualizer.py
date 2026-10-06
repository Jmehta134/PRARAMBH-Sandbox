from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt

class StateNode(QFrame):
    def __init__(self, state_name):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.label = QLabel(state_name)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.label)
        self.setFixedSize(180, 50)
        self.set_active(False)

    def set_active(self, is_active):
        if is_active:
            self.setStyleSheet("background-color: #0078D7; color: white; border-radius: 25px; border: 2px solid #005A9E;")
        else:
            self.setStyleSheet("background-color: #E5E5E5; color: #888888; border-radius: 25px; border: 2px solid #CCCCCC;")

class FSMVisualizerView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(15)
        
        title = QLabel("LIVE FSM STATE TRACKER")
        title.setStyleSheet("font-weight: bold; color: #555555; font-size: 11px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Mock States extracted from Verilog (e.g., FETCH, DECODE, EXECUTE)
        self.nodes = {}
        states = ["IDLE", "FETCH", "DECODE", "EXECUTE", "WRITEBACK"]
        
        for state in states:
            node = StateNode(state)
            self.nodes[state] = node
            layout.addWidget(node)
            
            # Draw a stylized down-arrow between nodes
            if state != states[-1]:
                arrow = QLabel("↓")
                arrow.setAlignment(Qt.AlignCenter)
                arrow.setStyleSheet("color: #ADADAD; font-size: 20px; font-weight: bold;")
                layout.addWidget(arrow)
                
        # Set default active state
        self.nodes["IDLE"].set_active(True)

    def update_active_state(self, current_state_str):
        """API to highlight the active state based on Verilog simulation"""
        for name, node in self.nodes.items():
            node.set_active(name == current_state_str)