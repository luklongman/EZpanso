# EZpanso - Product Requirements Document (PRD)

## 1. Product Overview

### 1.1 Product Name

**EZpanso** - A modern GUI for managing Espanso text expansion snippets

### 1.2 Product Vision

To provide a user-friendly, efficient graphical interface for managing Espanso configuration files, making text expansion snippet management accessible and streamlined for all users.

### 1.3 Product Goals

- Simplify Espanso snippet management through a modern GUI
- Provide multiple UI framework options (PyQt6, Tkinter) for different deployment needs
- Enable efficient keyboard-driven workflow for power users
- Ensure reliable data persistence and automatic saving
- Minimize application size for easy distribution

## 2. Target Users

### 2.1 Primary Users

- **Power Users**: Developers, writers, and professionals who use extensive text expansions
- **Casual Users**: Individuals who want a simple way to manage basic text shortcuts
- **System Administrators**: Users managing Espanso configurations across multiple systems

### 2.2 User Personas

- **Alex the Developer**: Uses hundreds of code snippets, needs fast keyboard navigation
- **Sarah the Writer**: Manages templates and frequently used phrases
- **Mike the Admin**: Deploys and maintains Espanso across team environments

## 3. Core Features & Requirements

### 3.1 Data Management (P0 - Critical)

#### 3.1.1 Espanso Configuration Loading

- **Requirement**: Auto-detect default Espanso configuration directory
- **Platforms**: macOS (`~/Library/Application Support/espanso/match`), Linux (`~/.config/espanso/match`)
- **Fallback**: Manual directory selection via file browser
- **Status**: ✅ Implemented

#### 3.1.2 YAML File Parsing

- **Requirement**: Parse and display all YAML files in match directory
- **Structure**: Support standard Espanso YAML format with `matches` array
- **Error Handling**: Graceful handling of malformed YAML files
- **Status**: ✅ Implemented

#### 3.1.3 Auto-Save Functionality

- **Requirement**: Automatic saving of changes without user intervention
- **Trigger**: Save on any modification (add, edit, delete)
- **Background**: Use worker threads to prevent UI blocking
- **Status**: ✅ Implemented

### 3.2 Snippet Management (P0 - Critical)

#### 3.2.1 View Snippets

- **Layout**: Table view with columns: Trigger, Replace Text
- **Preview**: Truncate long replacement text with "..." indicator
- **Sorting**: Sortable by trigger name
- **Status**: ✅ Implemented

#### 3.2.2 Add New Snippets

- **Method 1**: Dialog-based creation (✅ Implemented)
- **Method 2**: Inline table editing with empty bottom row (✅ Implemented)
- **Validation**: Check for duplicate triggers within same category
- **Status**: ✅ Implemented

#### 3.2.3 Edit Existing Snippets

- **Method 1**: Dialog-based editing (✅ Implemented)
- **Method 2**: Inline table editing (✅ Implemented)
- **Multiline Support**: Handle multiline replacement text
- **Status**: ✅ Implemented

#### 3.2.4 Delete Snippets

- **Selection**: Single and multiple snippet deletion
- **Confirmation**: Custom dialog with "Delete {count}?" message
- **Status**: ✅ Implemented

### 3.3 Category Management (P0 - Critical)

#### 3.3.1 Category Display

- **Interface**: Dropdown/ComboBox showing all YAML files
- **Format**: Display user-friendly names (filename without .yml)
- **Status**: ✅ Implemented

#### 3.3.2 Create New Categories

- **Trigger**: "Add new Category..." option in dropdown
- **Dialog**: Title input with path preview
- **Validation**: Check for valid filename characters
- **Status**: ✅ Implemented

#### 3.3.3 Delete Categories

- **Confirmation**: Custom dialog "Delete {category}?"
- **Cleanup**: Remove from UI and filesystem
- **Status**: ✅ Implemented

### 3.4 Keyboard Navigation (P1 - High Priority)

#### 3.4.1 Basic Navigation

- **Up/Down Arrows**: Navigate between table rows
- **Enter**: Edit selected snippet
- **Escape**: Cancel selection/operation
- **Status**: ✅ Implemented

#### 3.4.2 Action Shortcuts

- **Cmd+N** (macOS) / **Ctrl+N**: Add new snippet
- **Cmd+Shift+N** / **Ctrl+Shift+N**: New category
- **Cmd+S** / **Ctrl+S**: Save all changes
- **Cmd+R** / **Ctrl+R**: Refresh data
- **Delete**: Remove selected snippets
- **Status**: ✅ Implemented

#### 3.4.3 Selection Management

- **Shift+Up/Down**: Multi-select snippets
- **Cmd+A** / **Ctrl+A**: Select all
- **Status**: ✅ Implemented

### 3.5 User Interface (P1 - High Priority)

#### 3.5.1 Main Window Layout

- **Top**: Category selector dropdown
- **Center**: Snippet table (resizable columns)
- **Bottom**: Action buttons, status bar
- **Size**: Default 1000x600, resizable
- **Status**: ✅ Implemented

#### 3.5.2 Menu System

- **File Menu**: Open Directory, Add Snippet, New Category, Save, Refresh
- **Edit Menu**: Standard editing operations
- **Status**: ✅ Implemented

#### 3.5.3 Status Feedback

- **Status Bar**: Show current operation, snippet counts, errors
- **Progress**: Loading indicators for background operations
- **Status**: ✅ Implemented

## 4. Technical Architecture

### 4.1 Framework Options

#### 4.1.1 PyQt6 Version (Primary)

- **File**: `main.py`
- **Features**: Full-featured, modern UI components
- **Target**: Desktop power users
- **Size**: Larger executable (~50MB+)
- **Status**: ✅ Production Ready

#### 4.1.2 Tkinter Version (Lightweight)

- **File**: `main_tkinter.py`
- **Features**: Basic functionality, smaller footprint
- **Target**: Minimal installations, simple deployments
- **Size**: Smaller executable (~10MB)
- **Status**: ✅ Basic Implementation

#### 4.1.3 Minimal PyQt6 Version

- **File**: `main_minimal.py`
- **Features**: Reduced PyQt6 modules for smaller size
- **Target**: Balance between features and size
- **Status**: 🔄 In Development

### 4.2 Core Modules

#### 4.2.1 Data Model (`data_model.py`)

- **Snippet Class**: Represents individual text expansion rules
- **State Tracking**: Modified, new, and deleted states
- **Validation**: Trigger uniqueness, format validation
- **Status**: ⚠️ Needs Completion

#### 4.2.2 File Handler (`file_handler.py`)

- **YAML Operations**: Load, parse, save Espanso configuration files
- **Path Management**: Cross-platform directory handling
- **Error Handling**: Graceful failure recovery
- **Status**: ⚠️ Needs Completion

#### 4.2.3 Constants (`constants.py`)

- **Configuration**: UI labels, shortcuts, default paths
- **Localization Ready**: Centralized text for future i18n
- **Status**: ✅ Complete

#### 4.2.4 Threading (`qt_data_loader.py`)

- **Background Operations**: Non-blocking file I/O
- **Progress Signals**: UI feedback for long operations
- **Status**: ✅ Complete

### 4.3 Build System

#### 4.3.1 PyInstaller Specifications

- **Multiple Targets**: Separate specs for each UI version
- **Size Optimization**: Exclude unnecessary modules
- **Cross-Platform**: Support macOS, Linux, Windows
- **Status**: ✅ Multiple configs available

## 5. Milestones & Roadmap

### 5.1 Milestone 1: Core Stability (CURRENT)

**Target**: Complete basic functionality with reliable data handling

**Tasks**:

- [ ] Complete `data_model.py` implementation
- [ ] Complete `file_handler.py` implementation  
- [ ] Fix incomplete method implementations in main files
- [ ] Comprehensive error handling
- [ ] Unit tests for core functions

**Success Criteria**:

- All basic CRUD operations work reliably
- No data loss under normal operations
- Proper error messages for edge cases

### 5.2 Milestone 2: Enhanced UX

**Target**: Improve user experience and keyboard navigation

**Tasks**:

- [ ] Optimize keyboard navigation responsiveness
- [ ] Implement search/filter functionality
- [ ] Add drag-and-drop snippet reordering
- [ ] Improve inline editing experience
- [ ] Add undo/redo functionality

**Success Criteria**:

- Smooth keyboard-only workflow
- Fast snippet lookup and filtering
- Intuitive editing experience

### 5.3 Milestone 3: Advanced Features

**Target**: Power user features and customization

**Tasks**:

- [ ] Snippet import/export functionality
- [ ] Backup and restore capabilities
- [ ] Custom keyboard shortcuts
- [ ] Snippet templates and variables
- [ ] Bulk editing operations

**Success Criteria**:

- Complete workflow automation
- Advanced snippet management
- Customizable user preferences

### 5.4 Milestone 4: Polish & Distribution

**Target**: Production-ready application

**Tasks**:

- [ ] Complete documentation
- [ ] Installer packages for all platforms
- [ ] Performance optimization
- [ ] Accessibility improvements
- [ ] Automated testing pipeline

**Success Criteria**:

- Easy installation on all platforms
- Professional documentation
- Stable, performant application

## 6. Success Metrics

### 6.1 Functional Metrics

- **Reliability**: 99%+ operation success rate
- **Performance**: < 2s startup time, < 500ms operation response
- **Compatibility**: Support Espanso v0.7.3+ configuration format

### 6.2 User Experience Metrics

- **Efficiency**: Complete snippet CRUD cycle in < 30 seconds
- **Accessibility**: 100% keyboard navigation coverage
- **Learning Curve**: New users productive in < 5 minutes

### 6.3 Technical Metrics

- **Executable Size**: PyQt6 < 100MB, Tkinter < 20MB
- **Memory Usage**: < 50MB RAM during normal operation
- **Cross-Platform**: Support macOS 10.14+, Ubuntu 18.04+, Windows 10+

## 7. Risks & Mitigation

### 7.1 High Risk Items

1. **Incomplete Core Implementation**
   - **Risk**: Missing functionality in data_model.py and file_handler.py
   - **Impact**: Application instability, data loss
   - **Mitigation**: Prioritize completion of core modules

2. **YAML Parsing Complexity**
   - **Risk**: Espanso format changes breaking compatibility
   - **Impact**: Application cannot read/write configurations
   - **Mitigation**: Comprehensive testing with various YAML formats

### 7.2 Medium Risk Items

1. **Platform Differences**
   - **Risk**: Path handling, file permissions vary by OS
   - **Impact**: Application fails on some platforms
   - **Mitigation**: Extensive cross-platform testing

2. **Performance with Large Datasets**
   - **Risk**: Slow UI with hundreds of snippets
   - **Impact**: Poor user experience
   - **Mitigation**: Implement pagination, lazy loading

### 7.3 Low Risk Items

1. **UI Framework Limitations**
   - **Risk**: Some advanced features may be harder in Tkinter
   - **Impact**: Feature disparity between versions
   - **Mitigation**: Focus core features in all versions

## 8. Dependencies

### 8.1 External Dependencies

- **PyQt6**: 6.5.0+ (PyQt6 versions)
- **PyYAML**: 6.0+ (YAML parsing)
- **Python**: 3.11+ (runtime requirement)

### 8.2 Development Dependencies

- **PyInstaller**: 6.13.0+ (executable building)
- **Poetry**: Package management and build system

### 8.3 Runtime Dependencies

- **Espanso**: Compatible with v0.7.3+ configuration format
- **Operating System**: macOS 10.14+, Ubuntu 18.04+, Windows 10+

## 9. Future Considerations

### 9.1 Potential Enhancements

- Cloud synchronization of snippets
- Snippet sharing and community features
- Plugin system for custom functionality
- Integration with other text expansion tools
- Web-based interface option

### 9.2 Scalability Considerations

- Database backend for large snippet collections
- Multi-user support
- Enterprise deployment options
- API for programmatic access

---

**Document Version**: 1.0  
**Last Updated**: May 31, 2025  
**Status**: Living Document - Subject to Updates
