"""
Theme Loader Utility
Loads custom CSS for Trading Dashboard to match LocalAI Finance website aesthetic
"""

import streamlit as st
from pathlib import Path


def load_custom_css():
    """
    Load custom CSS file and inject into Streamlit app

    Returns:
        bool: True if CSS loaded successfully, False otherwise
    """
    try:
        # Get path to custom CSS file
        css_file = Path(__file__).parent.parent / "assets" / "custom.css"

        if not css_file.exists():
            st.error(f"Custom CSS file not found: {css_file}")
            return False

        # Read CSS file
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Inject CSS into Streamlit app
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

        return True

    except Exception as e:
        st.error(f"Error loading custom CSS: {e}")
        return False


def apply_gradient_text(text: str, tag: str = "h1") -> str:
    """
    Apply gradient text effect to text

    Args:
        text: Text to apply gradient to
        tag: HTML tag to wrap text in (h1, h2, h3, p, span)

    Returns:
        str: HTML with gradient text effect
    """
    return f'<{tag} class="gradient-text">{text}</{tag}>'


def create_status_badge(status: str, text: str = None) -> str:
    """
    Create a status badge with appropriate color

    Args:
        status: Status type ('healthy', 'warning', 'error')
        text: Custom text for badge (defaults to status)

    Returns:
        str: HTML for status badge
    """
    if text is None:
        text = status.upper()

    status_class = f"status-{status.lower()}"
    return f'<span class="{status_class}">{text}</span>'


def create_glass_card(content: str, hover: bool = True) -> str:
    """
    Wrap content in a glass morphism card

    Args:
        content: HTML content to wrap
        hover: Enable hover effect

    Returns:
        str: HTML with glass card styling
    """
    hover_class = "glass-card" if hover else "glass-card-no-hover"
    return f'<div class="{hover_class}">{content}</div>'


def add_animation(element_id: str, animation: str = "fade-in"):
    """
    Add animation class to element

    Args:
        element_id: ID of element to animate
        animation: Animation class ('fade-in', 'slide-up', 'glow-pulse')
    """
    return f"""
    <script>
        document.getElementById('{element_id}').classList.add('{animation}');
    </script>
    """


def get_color_palette():
    """
    Get color palette for charts and visualizations

    Returns:
        dict: Color palette matching website theme
    """
    return {
        'background': '#0F172A',
        'card': '#1E293B',
        'text_primary': '#F1F5F9',
        'text_secondary': '#94A3B8',
        'primary': '#6366F1',
        'secondary': '#8B5CF6',
        'accent': '#06B6D4',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'gradient': ['#6366F1', '#8B5CF6', '#06B6D4']
    }


def get_plotly_theme():
    """
    Get Plotly theme configuration matching website aesthetic

    Returns:
        dict: Plotly theme configuration
    """
    colors = get_color_palette()

    return {
        'template': 'plotly_dark',
        'layout': {
            'paper_bgcolor': colors['card'],
            'plot_bgcolor': colors['background'],
            'font': {
                'family': 'Inter, sans-serif',
                'color': colors['text_primary'],
                'size': 12
            },
            'title': {
                'font': {
                    'family': 'Orbitron, sans-serif',
                    'size': 24,
                    'color': colors['text_primary']
                }
            },
            'xaxis': {
                'gridcolor': 'rgba(148, 163, 184, 0.1)',
                'linecolor': 'rgba(148, 163, 184, 0.2)',
                'tickfont': {'color': colors['text_secondary']}
            },
            'yaxis': {
                'gridcolor': 'rgba(148, 163, 184, 0.1)',
                'linecolor': 'rgba(148, 163, 184, 0.2)',
                'tickfont': {'color': colors['text_secondary']}
            },
            'legend': {
                'bgcolor': 'rgba(30, 41, 59, 0.6)',
                'bordercolor': 'rgba(255, 255, 255, 0.1)',
                'font': {'color': colors['text_primary']}
            }
        },
        'colorway': [
            colors['primary'],
            colors['secondary'],
            colors['accent'],
            colors['success'],
            colors['warning'],
            colors['danger']
        ]
    }


# Convenience functions for common UI patterns
def render_hero_section(title: str, subtitle: str = None):
    """Render hero section with gradient text"""
    hero_html = f"""
    <div class="hero-section fade-in">
        <h1 class="gradient-text">{title}</h1>
        {f'<p style="font-size: 1.25rem; color: var(--text-secondary); margin-top: 1rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = None, status: str = None):
    """Render a metric card with glass morphism"""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ''
    status_html = create_status_badge(status) if status else ''

    card_html = f"""
    <div class="glass-card metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value gradient-text">{value}</div>
        {delta_html}
        {status_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
