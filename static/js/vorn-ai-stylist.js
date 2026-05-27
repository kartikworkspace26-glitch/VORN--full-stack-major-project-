/**
 * VORN — AI Stylist Chatbot Widget
 * Manages the floating luxury stylist UI, model selection, chat history, and REST API communication.
 */
document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // Create Chatbot DOM elements dynamically or match existing
  const chatToggle = document.getElementById('ai-stylist-toggle');
  const chatWidget = document.getElementById('ai-stylist-widget');
  const chatClose = document.getElementById('ai-stylist-close');
  const chatForm = document.getElementById('ai-stylist-form');
  const chatInput = document.getElementById('ai-stylist-input');
  const chatMessages = document.getElementById('ai-stylist-messages');
  const modelSelect = document.getElementById('ai-stylist-model');

  if (!chatToggle || !chatWidget) return;

  // Toggle Chat Widget Open/Close
  chatToggle.addEventListener('click', () => {
    chatWidget.classList.toggle('open');
    chatToggle.classList.toggle('active');
    if (chatWidget.classList.contains('open')) {
      chatInput.focus();
      // Send greeting if empty
      if (chatMessages.children.length === 0) {
        addMessage('Hello. I am your VORN AI Stylist. Select a model above, and let me help you curate your perfect silhouette or fragrance. What look are we styling today?', 'assistant');
      }
    }
  });

  chatClose.addEventListener('click', () => {
    chatWidget.classList.remove('open');
    chatToggle.classList.remove('active');
  });

  // Handle Form Submission
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msgText = chatInput.value.trim();
    if (!msgText) return;

    // Add user message
    addMessage(msgText, 'user');
    chatInput.value = '';

    // Add loading indicator
    const loadingEl = addLoadingIndicator();

    try {
      const activeModel = modelSelect ? modelSelect.value : 'gemini-nano-banana-pro';
      const csrfToken = getCookie('csrftoken');

      const response = await fetch('/api/ai-stylist/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          message: msgText,
          model: activeModel
        })
      });

      loadingEl.remove();

      if (response.ok) {
        const data = await response.json();
        addMessage(data.reply || 'I apologize, but I could not formulate a reply at this moment.', 'assistant');
      } else {
        addMessage('I apologize, my styling parlor seems to be temporarily offline. Please try again shortly.', 'assistant');
      }
    } catch (err) {
      console.error(err);
      loadingEl.remove();
      addMessage('Network connection error. Please verify your connection.', 'assistant');
    }
  });

  // Helpers
  function addMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `chat-message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = formatMessage(text);
    
    msg.appendChild(bubble);
    chatMessages.appendChild(msg);
    scrollToBottom();
    return msg;
  }

  function addLoadingIndicator() {
    const msg = document.createElement('div');
    msg.className = 'chat-message assistant loading-indicator';
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble loading-dots';
    bubble.innerHTML = '<span>.</span><span>.</span><span>.</span>';
    
    msg.appendChild(bubble);
    chatMessages.appendChild(msg);
    scrollToBottom();
    return msg;
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function formatMessage(text) {
    // 1. Clean HTML characters to prevent XSS
    let clean = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // 2. Format Markdown links: [text](/url/) to HTML links
    // Supporting standard slash link patterns
    clean = clean.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="chat-product-link">$1</a>');

    // 3. Format Bold: **text** to <strong>
    clean = clean.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 4. Format Bullets
    clean = clean.replace(/^\s*[•\-*]\s*(.+)$/gm, '<li>$1</li>');
    
    // Wrap lists if bullets are present
    if (clean.includes('<li>')) {
      clean = clean.replace(/(<li>.*<\/li>)/gs, '<ul class="chat-bullets">$1</ul>');
    }

    // 5. Convert newlines to line breaks (outside lists to avoid double breaks)
    clean = clean.replace(/\n/g, '<br>');

    return clean;
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
