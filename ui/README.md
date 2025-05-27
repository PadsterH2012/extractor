# AI-Powered Extraction v3 Web UI

> **Modern web interface for PDF analysis and extraction**
> **Status**: 🚀 Ready to Use
> **Technology**: Flask + Bootstrap + JavaScript

## 🎯 Overview

The Web UI provides a user-friendly interface for the AI-Powered Extraction v3 system, allowing you to:

1. **📄 Upload PDFs**: Drag-and-drop or browse for PDF files
2. **🤖 AI Analysis**: Analyze content with Claude AI, OpenAI, or Mock AI
3. **⚙️ Content Extraction**: Extract and categorize PDF content
4. **💾 Database Import**: Import to ChromaDB and/or MongoDB
5. **📊 Real-time Status**: Monitor system health and progress

## 🚀 Quick Start

### 1. Start the Web UI
```bash
cd "/mnt/network_repo/extractor"
python ui/start_ui.py
```

### 2. Open in Browser
- **Local**: http://localhost:5000
- **Network**: http://0.0.0.0:5000

### 3. Upload and Process
1. Drag PDF file to upload area
2. Select AI provider (Claude recommended)
3. Click "Analyze PDF"
4. Click "Extract Content"
5. Choose "Import to ChromaDB" or "Import to MongoDB"

## 🔧 Features

### 📤 File Upload
- **Drag & Drop**: Modern drag-and-drop interface
- **File Validation**: PDF-only with size limits (100MB max)
- **Progress Tracking**: Visual progress indicators
- **File Info**: Display filename and size

### 🤖 AI Analysis
- **Multiple Providers**: Claude AI, OpenAI, Local LLM, Mock AI
- **Real-time Analysis**: Live progress updates
- **Confidence Scoring**: AI confidence levels displayed
- **Game Detection**: Automatic game type and book identification

### ⚙️ Content Extraction
- **Smart Categorization**: AI-powered content classification
- **Progress Monitoring**: Real-time extraction progress
- **Summary Statistics**: Pages, words, sections count
- **Category Distribution**: Visual breakdown of content types

### 💾 Database Integration
- **ChromaDB Import**: Vector database integration
- **MongoDB Support**: Planned integration
- **Download Results**: Export extraction data as JSON
- **Import Status**: Success/error feedback

### 📊 System Monitoring
- **Health Check**: ChromaDB connection status
- **AI Provider Status**: Check API key configuration
- **Session Tracking**: Active sessions and completions
- **Real-time Updates**: Live system status

## 🎨 User Interface

### Modern Design
- **Bootstrap 5**: Responsive, mobile-friendly design
- **Font Awesome**: Professional icons throughout
- **Custom CSS**: Polished animations and transitions
- **Toast Notifications**: Non-intrusive status messages

### Workflow Steps
1. **Upload** (Blue): File selection and upload
2. **Analysis** (Green): AI-powered content analysis
3. **Extraction** (Yellow): Content extraction and categorization
4. **Import** (Info): Database import options

### Progress Tracking
- **Visual Indicators**: Step-by-step progress tracking
- **Status Icons**: Completed, active, and pending states
- **Smooth Animations**: Professional transitions between steps

## 🔧 Configuration

### AI Providers
```bash
# Claude AI (Recommended)
export ANTHROPIC_API_KEY="sk-ant-your-key"

# OpenAI
export OPENAI_API_KEY="sk-your-key"

# Local LLM
export LOCAL_LLM_URL="http://localhost:11434"
export LOCAL_LLM_MODEL="llama2"

# Mock AI (No configuration needed)
```

### ChromaDB
- **Server**: Automatically detected
- **Collections**: Auto-created during import
- **Status**: Real-time connection monitoring

### MongoDB
```bash
# MongoDB Configuration
export MONGODB_HOST="10.202.28.46"
export MONGODB_PORT="27017"
export MONGODB_DATABASE="rpger"

# Optional: Authentication
export MONGODB_USERNAME="your_username"
export MONGODB_PASSWORD="your_password"
```

## 📁 File Structure

```
ui/
├── app.py                 # Main Flask application
├── start_ui.py           # Startup script with dependency checks
├── requirements.txt      # UI-specific dependencies
├── README.md            # This documentation
├── templates/
│   └── index.html       # Main UI template
└── static/
    ├── css/
    │   └── style.css    # Custom styles and animations
    └── js/
        └── app.js       # JavaScript application logic
```

## 🛠️ Technical Details

### Backend (Flask)
- **File Upload**: Secure file handling with validation
- **Session Management**: Temporary session storage for workflow
- **API Integration**: Direct integration with extraction modules
- **Error Handling**: Comprehensive error catching and reporting

### Frontend (JavaScript)
- **AJAX Requests**: Asynchronous communication with backend
- **Progress Updates**: Real-time UI updates
- **File Handling**: Drag-and-drop with validation
- **Toast Notifications**: User-friendly status messages

### Security
- **File Validation**: PDF-only with size limits
- **Secure Filenames**: Werkzeug secure filename handling
- **Temporary Storage**: Automatic cleanup of uploaded files
- **Input Sanitization**: Protection against malicious inputs

## 📊 Performance

### File Handling
- **Upload Limit**: 100MB maximum file size
- **Supported Formats**: PDF only
- **Processing**: Streaming for large files
- **Cleanup**: Automatic temporary file removal

### Response Times
- **File Upload**: ~1-5 seconds depending on size
- **AI Analysis**: ~5-10 seconds with real AI providers
- **Content Extraction**: ~30-60 seconds for typical PDFs
- **Database Import**: ~5-15 seconds depending on content size

## 🔍 Troubleshooting

### Common Issues

#### UI Won't Start
```bash
# Check if you're in the right directory
cd "/mnt/network_repo/rule_book/extraction tool/Extractionv3"

# Install Flask if missing
pip install flask

# Run startup script
python ui/start_ui.py
```

#### AI Analysis Fails
- **Check API Keys**: Ensure environment variables are set
- **Use Mock AI**: Fallback option that works without API keys
- **Check Network**: Ensure internet connectivity for cloud AI

#### ChromaDB Import Fails
- **Check ChromaDB Server**: Ensure server is running at 10.202.28.49:8000
- **Check Permissions**: Ensure write access to ChromaDB
- **Check Collection Names**: Verify collection naming conventions

#### File Upload Issues
- **File Size**: Ensure PDF is under 100MB
- **File Type**: Only PDF files are supported
- **Browser**: Try different browser if upload fails

### Debug Mode
The UI runs in debug mode by default, providing:
- **Detailed Error Messages**: Full stack traces in browser
- **Auto-reload**: Automatic restart when code changes
- **Console Logging**: Detailed logs in terminal

## 🔗 Integration

### With Extraction v3
- **Direct Module Import**: Uses existing extraction modules
- **Shared Configuration**: Inherits AI and database settings
- **Session Compatibility**: Works with existing extraction workflows

### With ChromaDB
- **Auto-detection**: Automatically finds ChromaDB server
- **Collection Management**: Creates collections as needed
- **Vector Import**: Proper vector database formatting

### With MongoDB
- **Full Integration**: MongoDB import now available
- **Dual Database**: Works alongside ChromaDB for complete coverage
- **MCP Compatibility**: Works with existing MCP tools
- **Monster Data**: Special handling for monster imports
- **Schema Conversion**: Automatic ChromaDB to MongoDB format conversion

## 🎉 Success Examples

### Typical Workflow
```
1. Upload: tsr2010-players-handbook.pdf (15MB)
2. Analysis: Claude AI detects "D&D 1st PHB" (95% confidence)
3. Extraction: 125 pages, 133k words, 120 sections
4. Import: ChromaDB collection "dnd_1st_phb" created
5. Result: Ready for vector search and analysis
```

### Performance Metrics
- **Total Time**: ~90 seconds for complete workflow
- **AI Analysis**: ~5 seconds with Claude AI
- **Content Extraction**: ~60 seconds for 125-page PDF
- **ChromaDB Import**: ~10 seconds for 120 sections

---

**🎉 The Web UI provides a modern, user-friendly interface for the powerful AI-Powered Extraction v3 system, making PDF analysis and extraction accessible to all users!**
