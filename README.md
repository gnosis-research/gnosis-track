# Gnosis-Track

🚀 **Open Source Centralized Logging for Bittensor Subnets and AI Validators**

A modern, high-performance logging solution designed specifically for Bittensor subnet validators with real-time monitoring, secure storage, and easy integration.

## ✨ Key Features

- **🔥 Drop-in Integration**: Simple 3-line setup for existing validators
- **📊 Real-time UI**: Live log streaming and monitoring dashboard  
- **🔒 Secure Storage**: AES256 encryption with SeaweedFS backend
- **🏠 Self-Hosted**: Deploy your own infrastructure (free)
- **☁️ Managed Service**: Coming soon - we handle everything (paid)
- **📈 Scalable**: Handle millions of log entries efficiently

## 🚀 Quick Start

### For Subnet Validators

```python
# Replace your existing logging with 3 lines:
import gnosis_track

gnosis_track.init(
    config=config,
    wallet=wallet,
    project="my-subnet-validators",
    uid=uid
)

# All your existing bt.logging calls now stream to Gnosis-Track automatically!
bt.logging.info("This goes to Gnosis-Track")

# Optional manual logging
gnosis_track.log({"step": step, "scores": scores})
```

### For Subnet Owners

Deploy your own logging infrastructure:

```bash
# Install
pip install gnosis-track

# Deploy SeaweedFS + UI
gnosis-track deploy --subnet-id 13

# Share endpoint with your validators
echo "Point validators to: https://your-server.com:8333"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Validator Integration                   │
├─────────────────────────────────────────────────────────┤
│    Automatic Log Capture  │  Manual Logging API        │
├─────────────────────────────────────────────────────────┤
│              SeaweedFS S3-Compatible Storage            │
├─────────────────────────────────────────────────────────┤
│                    Real-time Web UI                     │
└─────────────────────────────────────────────────────────┘
```

## 📊 Web UI

Start the web interface:

```bash
gnosis-track ui --port 8081
```

Features:
- **Real-time streaming**: Watch logs as they arrive
- **Multi-validator**: Monitor all subnet validators
- **Advanced filtering**: Search by level, validator, time
- **Export options**: JSON, CSV formats

## 🔧 Configuration

### Self-Hosted Setup

```python
# In your validator config
gnosis_track_endpoint = "your-seaweed-server.com:8333"
gnosis_track_bucket = "subnet-13-logs"
gnosis_track_access_key = "admin"
gnosis_track_secret_key = "your-secret"
```

### Managed Service (Coming Soon)

```python
# Point to our hosted service
api_key = "gt_xxxxx"  # Get from gnosis-track.com
endpoint = "https://api.gnosis-track.com"
```

## 🎯 Business Model

- **🏠 Self-Hosted**: Free - deploy your own SeaweedFS + UI
- **☁️ Managed Service**: Paid - we handle infrastructure, scaling, backups

## 🛠️ Installation

```bash
# Install the package
pip install gnosis-track

# For self-hosted deployment
gnosis-track install seaweedfs

# Start UI server
gnosis-track ui
```

## 📚 Examples

Check the `examples/` directory for:
- Basic validator integration
- Custom configuration
- Monitoring and alerting
- Advanced usage patterns

## 🧪 Testing

```bash
# Run test data generators
python tests/comprehensive_test_data.py
python tests/infinite_random_logs.py

# Open UI to see test data
gnosis-track ui --port 8081
```

## 🤝 Contributing

We welcome contributions from the open source community! Here's how to get started:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Setup

```bash
# Clone the repo
git clone https://github.com/gnosis-research/gnosis-track.git
cd gnosis-track

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Start development UI
python -m gnosis_track.ui.server
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/gnosis-research/gnosis-track/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/gnosis-research/gnosis-track/discussions)
- 📧 **Contact**: support@gnosis-research.com
- 📖 **Documentation**: Coming soon

## 🎯 Roadmap

### ✅ Phase 1: Core Features (Completed)
- [x] SeaweedFS integration
- [x] Real-time web UI
- [x] Bittensor validator integration
- [x] Automatic log capture
- [x] Self-hosted deployment

### 🚧 Phase 2: Enhancement (In Progress)
- [ ] Managed service launch
- [ ] Advanced analytics dashboard
- [ ] Multi-subnet support
- [ ] Performance optimizations
- [ ] Mobile-responsive UI

### 📋 Phase 3: Scale (Planned)
- [ ] Enterprise features
- [ ] Third-party integrations
- [ ] Custom dashboard builder
- [ ] Advanced alerting system
- [ ] Multi-cloud support

## 🌟 Community

Join our growing community of Bittensor subnet operators and developers:

- **Contributors**: Thanks to all our contributors who make this project possible
- **Subnet Owners**: Share feedback and feature requests
- **Validators**: Help us test and improve the integration
- **Developers**: Contribute code, docs, and ideas

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=gnosis-research/gnosis-track&type=Date)](https://star-history.com/#gnosis-research/gnosis-track&Date)

---

**Made with ❤️ for the Bittensor community**

*Gnosis-Track is built by developers, for developers. We believe in open source, transparent logging, and empowering subnet owners with the tools they need to succeed.*