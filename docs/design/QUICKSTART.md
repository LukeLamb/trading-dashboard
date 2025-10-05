# Dashboard Redesign - Quick Start Guide

**Read this first!** This is your condensed action plan for the dashboard redesign.

---

## 📋 **What We're Doing**

Transforming the Trading Dashboard to match the LocalAI Finance website with:
- **Dark futuristic theme** (Indigo/Purple/Cyan colors)
- **Glass morphism design** (like the website)
- **Professional polish** for demo videos
- **Demo mode** for easy recording

---

## ⚡ **Implementation Order**

### **Phase 1: Theme Foundation** (2-3 hours)
1. Create `.streamlit/config.toml` with website colors
2. Build `src/dashboard/assets/custom.css` with glass morphism
3. Load fonts (Orbitron, Inter, JetBrains Mono)
4. Test theme loads correctly

**Deliverable:** Dashboard has website's dark theme

---

### **Phase 2: Page Redesign** (3-4 hours)
Redesign pages in order of importance:
1. **Overview** - Hero section, agent status cards
2. **Charts** - Dark Plotly theme, gradient accents
3. **Analytics** - System metrics, glass cards
4. **Alerts** - Glow effects by severity
5. **Agents** - Control interface
6. **Error Handling** - Diagnostic panels

**Deliverable:** All pages match website aesthetic

---

### **Phase 3: Demo Mode** (2-3 hours)
1. Create demo mode toggle
2. Add 5 pre-configured scenarios
3. Optimize for smooth recording
4. Test all scenarios

**Deliverable:** Demo-ready dashboard

---

### **Phase 4: Polish** (2-3 hours)
1. Test responsiveness (1920x1080 for recording)
2. Fix performance issues
3. Add smooth animations
4. Final QA pass

**Deliverable:** Production-ready for recording

---

## 🎨 **Design Tokens**

Copy-paste these exact values:

```python
# Colors
BACKGROUND = "#0F172A"          # Dark Slate
CARD_BG = "#1E293B"             # Lighter Slate
TEXT_PRIMARY = "#F1F5F9"        # Light Slate
TEXT_SECONDARY = "#94A3B8"      # Slate Gray
PRIMARY = "#6366F1"             # Indigo
SECONDARY = "#8B5CF6"           # Purple
ACCENT = "#06B6D4"              # Cyan
SUCCESS = "#10B981"             # Emerald
WARNING = "#F59E0B"             # Amber
DANGER = "#EF4444"              # Red

# Fonts
HEADING_FONT = "Orbitron"
BODY_FONT = "Inter"
CODE_FONT = "JetBrains Mono"

# Spacing
BORDER_RADIUS_SM = "8px"
BORDER_RADIUS_MD = "12px"
BORDER_RADIUS_LG = "16px"

# Glass Morphism
GLASS_BG = "rgba(30, 41, 59, 0.6)"
GLASS_BLUR = "blur(10px)"
GLASS_BORDER = "rgba(255, 255, 255, 0.1)"
```

---

## 🎯 **Success Checklist**

Before recording demos, verify:

- [ ] Dashboard opens with dark theme (no white flash)
- [ ] All text is readable (light on dark)
- [ ] Cards have glass morphism effect
- [ ] Charts use dark Plotly theme
- [ ] Buttons have hover effects
- [ ] Gradients match website
- [ ] Fonts match website (Orbitron/Inter)
- [ ] Animations are smooth (60fps)
- [ ] Demo mode works flawlessly
- [ ] No console errors

---

## 📹 **Demo Videos to Record**

After redesign is complete:

1. **Dashboard Overview** (60s) - Full walkthrough
2. **Real-time Data** (30s) - Charts updating
3. **Data Quality** (30s) - A-F grading system
4. **Multi-Source Failover** (30s) - Source switching
5. **System Monitoring** (30s) - Performance metrics

**Format:** 1920x1080, 30fps, MP4

---

## 🚀 **Next Steps**

1. **Review** the [Master Plan](./dashboard-redesign-master-plan.md) (comprehensive details)
2. **Start** with Phase 1, Step 1.1 (create `.streamlit/config.toml`)
3. **Test** frequently (run dashboard after each change)
4. **Ask** questions if anything is unclear

---

## 📚 **Key Documents**

- **This guide** - Quick reference
- [Master Plan](./dashboard-redesign-master-plan.md) - Complete roadmap (16 hours of detail)
- [Docs README](../README.md) - Documentation index

---

## ⏱️ **Time Estimate**

- **Minimum:** 8 hours (basic redesign)
- **Recommended:** 12 hours (polished redesign)
- **Maximum:** 16 hours (perfect polish + recording)

**Timeline:** 1-2 days of focused work

---

## 💡 **Tips**

1. **Start small:** Get the theme working first before redesigning components
2. **Test often:** Run `streamlit run src/dashboard/main.py` after each change
3. **Match exactly:** Use website color codes exactly (no "close enough")
4. **Mobile-first:** Even though recording at 1920x1080, keep responsive
5. **Performance matters:** Dashboard must be smooth for good recordings

---

## ❓ **Questions?**

Refer to the [Master Plan](./dashboard-redesign-master-plan.md) for detailed answers on:
- Technical implementation
- Component specifications
- Recording workflow
- Timeline breakdown

---

**Ready to start?** → Create `.streamlit/config.toml` with the theme colors above! 🚀

---

*LocalAI Finance - Dashboard Redesign Quick Start*
*Created: October 5, 2025*
