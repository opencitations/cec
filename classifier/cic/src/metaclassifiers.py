import torch
import torch.nn as nn
import torch.nn.functional as F

class MetaClassifierNoSection(nn.Module):
    def __init__(self):
        super(MetaClassifierNoSection, self).__init__()
        self.fc1 = nn.Linear(6, 32)
        self.bn1 = nn.BatchNorm1d(32)
        self.fc2 = nn.Linear(32, 128)
        self.bn2 = nn.BatchNorm1d(128)
        self.fc3 = nn.Linear(128, 3)
        self.dropout = nn.Dropout(0.7)

    def forward(self, x):
        x = F.gelu(self.fc1(x))
        x = self.bn1(x)
        x = self.dropout(x)
        x = F.gelu(self.fc2(x))
        x = self.bn2(x)
        x = self.dropout(x)
        x = self.fc3(x)
        x = F.softmax(x, dim=1)
        return x

class MetaClassifierSection(nn.Module):
    def __init__(self):
        super(MetaClassifierSection, self).__init__()
        self.fc1 = nn.Linear(6, 32)
        self.bn1 = nn.BatchNorm1d(32)
        self.fc2 = nn.Linear(32, 64)
        self.bn2 = nn.BatchNorm1d(64)
        self.fc3 = nn.Linear(64, 3)
        self.dropout = nn.Dropout(0.7)

    def forward(self, x):
        x = F.gelu(self.fc1(x))
        x = self.bn1(x)
        x = self.dropout(x)
        x = F.gelu(self.fc2(x))
        x = self.bn2(x)
        x = self.dropout(x)
        x = self.fc3(x)
        x = F.softmax(x, dim=1)
        return x