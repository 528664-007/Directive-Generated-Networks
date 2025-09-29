import torch
import torch.optim as optim
from torchvision import datasets, transforms
from model import VAE, loss_function

# Hyperparameters
batch_size = 128
epochs = 10
latent_dim = 20
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Data loader
transform = transforms.Compose([transforms.ToTensor()])
train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

# Model, optimizer
model = VAE(latent_dim=latent_dim).to(device)
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# Training loop
model.train()
for epoch in range(epochs):
    train_loss = 0
    for batch_idx, (data, _) in enumerate(train_loader):
        data = data.to(device)
        optimizer.zero_grad()
        recon_batch, mean, logvar = model(data)
        loss = loss_function(recon_batch, data, mean, logvar)
        loss.backward()
        train_loss += loss.item()
        optimizer.step()
    print(f"Epoch {epoch+1}/{epochs}, Loss: {train_loss / len(train_loader.dataset):.4f}")

# Save model
torch.save(model.state_dict(), 'vae_model.pth')
print("Model saved to vae_model.pth")