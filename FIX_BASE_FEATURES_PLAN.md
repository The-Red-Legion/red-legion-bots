# Fix Base Features Plan

## 🎯 Objective
Fix the core functionality of the Red Legion Discord bot, focusing on:
- Slash commands registration and execution
- Events module functionality  
- Mining module core features
- Database integration reliability

## 🔍 Current Issues Identified

### 1. Import System Issues
- **Problem**: Module imports failing due to path resolution issues
- **Impact**: Commands not loading properly, test failures
- **Files Affected**: 
  - `src/commands/events.py`
  - `src/commands/mining/core.py`
  - Database operations imports

### 2. Slash Command Registration Problems
- **Problem**: Mixed slash command architecture causing registration failures
- **Impact**: Commands not syncing with Discord, bot functionality broken
- **Files Affected**:
  - `src/commands/__init__.py`
  - Individual command modules

### 3. Database Integration Issues
- **Problem**: Database operations module not loading correctly
- **Impact**: Event creation, mining tracking, and data persistence failing
- **Files Affected**:
  - `src/database/operations.py`
  - Command modules that use database

### 4. Test Failures
- **Problem**: Modular system tests failing due to import issues
- **Impact**: CI/CD pipeline failing, deployment issues
- **Files Affected**:
  - `tests/test_modular_system.py`
  - `tests/test_advanced_system.py`

## 🛠️ Fix Plan

### Phase 1: Clean Up Import System
1. **Standardize import paths** across all command modules
2. **Fix database operations imports** to use consistent absolute imports
3. **Update sys.path handling** for reliable module loading
4. **Remove importlib usage** where standard imports work better

### Phase 2: Consolidate Slash Command Architecture
1. **Remove old prefix commands** and legacy files
2. **Standardize slash command decorators** across all modules
3. **Fix command registration system** in `__init__.py`
4. **Ensure all commands use "red-" prefix** consistently

### Phase 3: Fix Core Bot Features
1. **Events Module**: Fix event creation, listing, and management
2. **Mining Module**: Fix mining session tracking and payroll
3. **Admin Module**: Fix configuration and administrative commands
4. **Database Integration**: Ensure reliable database operations

### Phase 4: Resolve Test Issues
1. **Fix import tests** in modular system
2. **Update test expectations** for new architecture
3. **Ensure CI/CD pipeline** passes consistently
4. **Add proper error handling** in tests

## 📋 Implementation Steps

### Step 1: Import System Cleanup
- [ ] Fix `src/database/operations.py` imports
- [ ] Update `src/commands/events.py` import system
- [ ] Update `src/commands/mining/core.py` import system
- [ ] Standardize sys.path usage across modules

### Step 2: Command Architecture Consolidation
- [ ] Review and update `src/commands/__init__.py`
- [ ] Ensure all command files use consistent structure
- [ ] Remove any remaining old command files
- [ ] Verify slash command decorators

### Step 3: Core Feature Fixes
- [ ] Test and fix events module slash commands
- [ ] Test and fix mining module functionality
- [ ] Test and fix admin module commands
- [ ] Verify database operations work correctly

### Step 4: Test and Validation
- [ ] Run local tests to verify fixes
- [ ] Fix any remaining test failures
- [ ] Ensure CI/CD pipeline passes
- [ ] Test bot functionality end-to-end

## 🎯 Success Criteria
- [ ] All slash commands register successfully
- [ ] Events module creates and manages events correctly
- [ ] Mining module tracks sessions and calculates payroll
- [ ] Database operations work reliably
- [ ] All tests pass consistently
- [ ] CI/CD pipeline runs without errors

## 📁 Key Files to Focus On
1. `src/commands/__init__.py` - Command registration system
2. `src/commands/events.py` - Event management functionality
3. `src/commands/mining/core.py` - Mining session tracking
4. `src/commands/admin.py` - Administrative commands
5. `src/database/operations.py` - Database integration
6. `tests/test_modular_system.py` - Import and registration tests

## 🔧 Priority Order
1. **CRITICAL**: Fix import system and database operations
2. **HIGH**: Fix slash command registration
3. **HIGH**: Fix events and mining core functionality
4. **MEDIUM**: Fix test suite and CI/CD
5. **LOW**: Documentation and cleanup

This plan will systematically address the core issues preventing the bot from functioning properly while maintaining the slash command architecture we've built.
