/**
 * PyView Frontend Client
 *
 * Handles WebSocket communication, hierarchical element tree rendering,
 * client-side tab switching, expander state persistence, and widget event dispatching.
 */

(function () {
  'use strict';

  // DOM Elements
  const appRoot = document.getElementById('app-root');
  const sidebarRoot = document.getElementById('sidebar-root');
  const sidebarContent = sidebarRoot ? sidebarRoot.querySelector('.pv-sidebar-content') : null;
  const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
  const connBadge = document.getElementById('status-connection');
  const connText = document.getElementById('status-text');
  const runningBadge = document.getElementById('status-running');
  const btnRerun = document.getElementById('btn-rerun');
  const errorContainer = document.getElementById('error-container');
  const errorTraceback = document.getElementById('error-traceback');
  const btnDismissError = document.getElementById('btn-dismiss-error');

  let ws = null;
  let reconnectTimer = null;
  let reconnectAttempts = 0;
  let currentGeneration = 0;

  // Track values to prevent duplicate event dispatches
  const lastWidgetValues = new Map();

  // Track client-side active tab index per tabs container
  const activeTabsMap = new Map();

  // Track uncommitted values for batched forms
  const formValuesMap = new Map();

  function getWsUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const sessionId = sessionStorage.getItem('pyview_session_id');
    const searchParams = new URLSearchParams(window.location.search);
    if (sessionId) {
      searchParams.set('session_id', sessionId);
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return `${protocol}//${host}/_pyview/ws${query}`;
  }

  function setPageConfig(cfg) {
    if (!cfg) return;

    // Document Title
    if (cfg.page_title) {
      document.title = cfg.page_title;
    }

    // Favicon (supports emoji or image URL)
    if (cfg.page_icon) {
      let link = document.querySelector("link[rel~='icon']");
      if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
      }

      if (cfg.page_icon.length <= 4) {
        // Emoji icon -> SVG Favicon
        link.href = `data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>${encodeURIComponent(cfg.page_icon)}</text></svg>`;
      } else {
        link.href = cfg.page_icon;
      }
    }

    // Layout Width (wide vs centered)
    if (cfg.layout === 'wide') {
      document.body.classList.add('pv-layout-wide');
    } else {
      document.body.classList.remove('pv-layout-wide');
    }
  }

  function syncQueryParams(qp) {
    if (!qp || typeof qp !== 'object') return;
    const params = new URLSearchParams();
    Object.entries(qp).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') {
        params.set(k, String(v));
      }
    });
    const qs = params.toString();
    const newUrl = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    window.history.replaceState(null, '', newUrl);
  }

  function setConnectionStatus(status) {
    connBadge.className = 'pv-conn-badge';
    if (status === 'connected') {
      connBadge.classList.add('pv-conn-connected');
      connText.textContent = 'Connected';
    } else if (status === 'connecting') {
      connBadge.classList.add('pv-conn-connecting');
      connText.textContent = 'Connecting...';
    } else {
      connBadge.classList.add('pv-conn-disconnected');
      connText.textContent = 'Disconnected';
    }
  }

  function setRunningStatus(isRunning) {
    runningBadge.style.display = isRunning ? 'flex' : 'none';
  }

  function connect() {
    if (ws) {
      ws.close();
    }

    setConnectionStatus('connecting');
    const wsUrl = getWsUrl();

    try {
      ws = new WebSocket(wsUrl);
    } catch (e) {
      scheduleReconnect();
      return;
    }

    ws.onopen = function () {
      setConnectionStatus('connected');
      reconnectAttempts = 0;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    };

    ws.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        handleServerMessage(data);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err, event.data);
      }
    };

    ws.onclose = function () {
      setConnectionStatus('disconnected');
      setRunningStatus(false);
      scheduleReconnect();
    };

    ws.onerror = function (err) {
      console.warn('WebSocket error:', err);
      ws.close();
    };
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), 10000);
    reconnectAttempts++;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, delay);
  }

  function sendMessage(payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
    } else {
      console.warn('Cannot send message, WebSocket not connected:', payload);
    }
  }

  // Unified widget event dispatcher (with form batching support)
  function sendWidgetEvent(widgetKey, value, formId) {
    if (formId) {
      if (!formValuesMap.has(formId)) {
        formValuesMap.set(formId, {});
      }
      formValuesMap.get(formId)[widgetKey] = value;
      return;
    }
    sendMessage({
      type: 'widget_event',
      key: widgetKey,
      value: value,
    });
  }


  function handleServerMessage(data) {
    const type = data.type;

    if (type === 'connected') {
      if (data.session_id) {
        sessionStorage.setItem('pyview_session_id', data.session_id);
      }
    } else if (type === 'status') {
      setRunningStatus(data.status === 'running');
    } else if (type === 'error') {
      showError(data.error);
    } else if (type === 'render') {
      if (data.generation !== undefined && data.generation < currentGeneration) {
        return;
      }
      currentGeneration = data.generation || currentGeneration;
      hideError();

      if (data.page_config) {
        setPageConfig(data.page_config);
      }
      if (data.query_params) {
        syncQueryParams(data.query_params);
      }

      renderElementTree(data.elements || []);
    }
  }

  function showError(tracebackText) {
    errorTraceback.textContent = tracebackText || 'Unknown runtime error occurred.';
    errorContainer.style.display = 'block';
  }

  function hideError() {
    errorContainer.style.display = 'none';
  }

  // Formatting helper for write blocks
  function formatTextContent(raw) {
    if (!raw) return '';
    let escaped = raw
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    escaped = escaped.replace(/^### (.*$)/gim, '<h3 style="font-size:16px; margin: 8px 0 4px;">$1</h3>');
    escaped = escaped.replace(/^## (.*$)/gim, '<h2 style="font-size:18px; margin: 10px 0 6px;">$1</h2>');
    escaped = escaped.replace(/^# (.*$)/gim, '<h1 style="font-size:22px; margin: 12px 0 8px;">$1</h1>');

    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/_(.*?)_/g, '<em>$1</em>');
    escaped = escaped.replace(/^- (.*$)/gim, '<li style="margin-left: 18px;">$1</li>');
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background: var(--bg-subtle); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 13px;">$1</code>');

    return escaped.replace(/\n/g, '<br/>');
  }

  function renderChildren(children, parentNode) {
    reconcileChildren(children, parentNode);
  }

  function reconcileChildren(children, parentNode) {
    if (!children || !Array.isArray(children)) {
      parentNode.innerHTML = '';
      return;
    }

    const oldNodes = Array.from(parentNode.children);
    const oldNodeMap = new Map();
    oldNodes.forEach((node) => {
      const key = node.getAttribute('data-node-id') || node.id;
      if (key) {
        oldNodeMap.set(key, node);
      }
      node._pyview_keep = false;
    });

    children.forEach((childEl, idx) => {
      const childJson = JSON.stringify(childEl);
      const key = childEl.id;
      const existingNode = key ? oldNodeMap.get(key) : null;

      if (existingNode && existingNode._pyview_json === childJson) {
        existingNode._pyview_keep = true;
        if (parentNode.children[idx] !== existingNode) {
          parentNode.insertBefore(existingNode, parentNode.children[idx] || null);
        }
      } else {
        const newNode = createElementNode(childEl);
        if (newNode) {
          newNode.setAttribute('data-node-id', childEl.id);
          newNode._pyview_json = childJson;
          newNode._pyview_keep = true;
          if (existingNode && existingNode.parentNode === parentNode) {
            parentNode.replaceChild(newNode, existingNode);
          } else {
            parentNode.insertBefore(newNode, parentNode.children[idx] || null);
          }
        }
      }
    });

    oldNodes.forEach((node) => {
      if (!node._pyview_keep && node.parentNode === parentNode) {
        parentNode.removeChild(node);
      }
    });
  }

  function renderElementTree(elements) {
    const activeEl = document.activeElement;
    const activeWidgetId = activeEl ? activeEl.getAttribute('data-widget-id') : null;
    const selectionStart = activeEl && activeEl.selectionStart !== undefined ? activeEl.selectionStart : null;
    const selectionEnd = activeEl && activeEl.selectionEnd !== undefined ? activeEl.selectionEnd : null;

    // Check for sidebar container in element list
    const sidebarElement = elements.find((el) => el.type === 'sidebar');
    const mainElements = elements.filter((el) => el.type !== 'sidebar');

    // Render Sidebar
    if (sidebarElement && sidebarRoot && sidebarContent) {
      reconcileChildren(sidebarElement.children || [], sidebarContent);
      sidebarRoot.style.display = 'flex';
      if (btnToggleSidebar) btnToggleSidebar.style.display = 'flex';
    } else if (sidebarRoot) {
      sidebarRoot.style.display = 'none';
      if (btnToggleSidebar) btnToggleSidebar.style.display = 'none';
    }

    // Render Main App Canvas
    reconcileChildren(mainElements, appRoot);

    // Restore focus if element persists
    if (activeWidgetId) {
      const restored = document.querySelector(`[data-widget-id="${activeWidgetId}"]`);
      if (restored && restored !== document.activeElement) {
        restored.focus();
        if (selectionStart !== null && selectionEnd !== null && restored.setSelectionRange) {
          try {
            restored.setSelectionRange(selectionStart, selectionEnd);
          } catch (e) {}
        }
      }
    }
  }

  function createElementNode(el) {
    const node = _createElementNodeInternal(el);
    if (node && el && el.id) {
      node.setAttribute('data-node-id', el.id);
    }
    return node;
  }

  function _createElementNodeInternal(el) {
    const type = el.type;
    const id = el.id;
    const props = el.props || {};
    const children = el.children || [];

    // --- Layout Containers ---
    if (type === 'columns') {
      const row = document.createElement('div');
      row.className = 'pv-columns';
      row.id = id;

      children.forEach((colEl) => {
        const colNode = document.createElement('div');
        colNode.className = 'pv-column';
        colNode.id = colEl.id;
        const weight = (colEl.props && colEl.props.weight !== undefined) ? colEl.props.weight : 1;
        colNode.style.flex = `${weight} 1 0px`;

        renderChildren(colEl.children || [], colNode);
        row.appendChild(colNode);
      });

      return row;
    }

    if (type === 'tabs') {
      const container = document.createElement('div');
      container.className = 'pv-tabs-container';
      container.id = id;

      const headerList = document.createElement('div');
      headerList.className = 'pv-tab-header-list';

      const panesWrapper = document.createElement('div');
      panesWrapper.className = 'pv-tab-panes-wrapper';

      // Retrieve previously active tab index for this tabs container
      let activeIndex = activeTabsMap.get(id) || 0;
      if (activeIndex >= children.length) {
        activeIndex = 0;
      }

      const tabButtons = [];
      const tabPanes = [];

      children.forEach((tabEl, idx) => {
        const label = (tabEl.props && tabEl.props.label) || `Tab ${idx + 1}`;
        const btn = document.createElement('button');
        btn.className = `pv-tab-btn ${idx === activeIndex ? 'pv-tab-active' : ''}`;
        btn.textContent = label;

        const pane = document.createElement('div');
        pane.className = 'pv-tab-pane';
        pane.id = tabEl.id;
        pane.style.display = idx === activeIndex ? 'flex' : 'none';

        renderChildren(tabEl.children || [], pane);

        btn.addEventListener('click', (e) => {
          e.preventDefault();
          activeTabsMap.set(id, idx);

          tabButtons.forEach((b, i) => {
            if (i === idx) {
              b.classList.add('pv-tab-active');
            } else {
              b.classList.remove('pv-tab-active');
            }
          });

          tabPanes.forEach((p, i) => {
            p.style.display = i === idx ? 'flex' : 'none';
          });
        });

        tabButtons.push(btn);
        tabPanes.push(pane);

        headerList.appendChild(btn);
        panesWrapper.appendChild(pane);
      });

      container.appendChild(headerList);
      container.appendChild(panesWrapper);
      return container;
    }

    if (type === 'expander') {
      const details = document.createElement('details');
      details.className = 'pv-expander';
      details.id = id;
      const initialOpen = Boolean(props.expanded);
      details.open = initialOpen;
      lastWidgetValues.set(id, initialOpen);

      const summary = document.createElement('summary');
      summary.className = 'pv-expander-summary';
      summary.textContent = props.label || 'Details';

      const body = document.createElement('div');
      body.className = 'pv-expander-body';
      renderChildren(children, body);

      details.appendChild(summary);
      details.appendChild(body);

      // Only dispatch toggle event on user click interaction to prevent render loops
      summary.addEventListener('click', () => {
        setTimeout(() => {
          const currentOpen = details.open;
          const prev = lastWidgetValues.get(id);
          if (currentOpen !== prev) {
            lastWidgetValues.set(id, currentOpen);
            sendWidgetEvent(id, currentOpen);
          }
        }, 20);
      });

      return details;
    }

    if (type === 'card') {
      const card = document.createElement('div');
      card.className = 'pv-card';
      card.id = id;

      if (props.title) {
        const title = document.createElement('div');
        title.className = 'pv-card-title';
        title.textContent = props.title;
        card.appendChild(title);
      }

      renderChildren(children, card);
      return card;
    }

    if (type === 'form') {
      const formEl = document.createElement('div');
      formEl.className = 'pv-form-container';
      formEl.id = id;
      renderChildren(children, formEl);
      return formEl;
    }

    if (type === 'status_container') {
      const statusBox = document.createElement('div');
      const st = props.state || 'running';
      statusBox.className = `pv-status-container pv-status-${st} ${props.expanded ? 'pv-status-open' : ''}`;
      statusBox.id = id;

      const header = document.createElement('div');
      header.className = 'pv-status-header';

      const left = document.createElement('div');
      left.className = 'pv-status-header-left';

      const icon = document.createElement('span');
      if (st === 'running') {
        icon.className = 'pv-status-icon-running';
      } else if (st === 'complete') {
        icon.className = 'pv-status-icon-complete';
        icon.textContent = '✅';
      } else if (st === 'error') {
        icon.className = 'pv-status-icon-error';
        icon.textContent = '❌';
      }

      const label = document.createElement('span');
      label.className = 'pv-status-label';
      label.textContent = props.label || 'Status';

      left.appendChild(icon);
      left.appendChild(label);

      const chevron = document.createElement('span');
      chevron.className = 'pv-status-chevron';
      chevron.textContent = '▼';

      header.appendChild(left);
      header.appendChild(chevron);

      header.addEventListener('click', () => {
        statusBox.classList.toggle('pv-status-open');
      });

      const content = document.createElement('div');
      content.className = 'pv-status-content';
      renderChildren(children, content);

      statusBox.appendChild(header);
      statusBox.appendChild(content);
      return statusBox;
    }

    if (type === 'skeleton') {
      const skelBox = document.createElement('div');
      skelBox.className = 'pv-skeleton-box';
      skelBox.id = id;
      if (props.height) skelBox.style.height = props.height;
      if (props.width) skelBox.style.width = props.width;
      if (children && children.length > 0) {
        renderChildren(children, skelBox);
      }
      return skelBox;
    }

    // --- Content & Typography ---
    if (type === 'title') {
      const h1 = document.createElement('h1');
      h1.className = 'pv-title';
      h1.id = id;
      h1.textContent = props.text || '';
      return h1;
    }

    if (type === 'header') {
      const h2 = document.createElement('h2');
      h2.className = 'pv-header-el';
      h2.id = id;
      h2.textContent = props.text || '';
      return h2;
    }

    if (type === 'write') {
      const wrapper = document.createElement('div');
      wrapper.id = id;
      const contentType = props.content_type || 'text';

      if (contentType === 'json') {
        const pre = document.createElement('pre');
        pre.className = 'pv-code-block';
        const code = document.createElement('code');
        code.textContent = props.content || '';
        pre.appendChild(code);
        wrapper.appendChild(pre);
      } else if (contentType === 'html') {
        wrapper.className = 'pv-write-block';
        wrapper.innerHTML = props.content || '';
      } else {
        wrapper.className = 'pv-write-block';
        wrapper.innerHTML = formatTextContent(props.content || '');
      }
      return wrapper;
    }

    // --- Value & Trigger Widgets ---
    if (type === 'button') {
      const btn = document.createElement('button');
      btn.className = 'pv-btn';
      btn.id = id;
      btn.setAttribute('data-widget-id', id);
      btn.textContent = props.label || 'Button';

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        sendWidgetEvent(id, true);
      });

      return btn;
    }

    if (type === 'download_button') {
      const btn = document.createElement('button');
      btn.className = 'pv-download-btn';
      btn.id = id;
      btn.setAttribute('data-widget-id', id);
      btn.textContent = `📥 ${props.label || 'Download'}`;

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (props.data_url) {
          const link = document.createElement('a');
          link.href = props.data_url;
          link.download = props.file_name || 'download.txt';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
        sendMessage({
          type: 'widget_event',
          key: id,
          value: true,
          is_trigger: true,
        });
      });

      return btn;
    }

    if (type === 'link_button') {
      const a = document.createElement('a');
      a.className = 'pv-link-btn';
      a.id = id;
      a.href = props.url || '#';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = `${props.label || 'Link'} ↗`;
      return a;
    }

    if (type === 'form_submit_button') {
      const btn = document.createElement('button');
      btn.className = 'pv-form-submit-btn';
      btn.id = id;
      btn.setAttribute('data-widget-id', id);
      btn.textContent = props.label || 'Submit';

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const batch = formValuesMap.get(props.form_id) || {};
        sendMessage({
          type: 'form_submit',
          form_id: props.form_id,
          submit_key: id,
          values: batch,
        });
      });

      return btn;
    }

    if (type === 'chat_input') {
      const wrapper = document.createElement('div');
      wrapper.className = 'pv-chat-input-container';
      wrapper.id = id;

      const inp = document.createElement('input');
      inp.className = 'pv-chat-input-field';
      inp.placeholder = props.placeholder || 'Ask a question...';

      const btn = document.createElement('button');
      btn.className = 'pv-chat-send-btn';
      btn.textContent = 'Send ↗';

      const submitChat = () => {
        const text = inp.value.trim();
        if (!text) return;
        inp.value = '';
        sendMessage({
          type: 'widget_event',
          key: id,
          value: text,
          is_trigger: true,
        });
      };

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        submitChat();
      });

      inp.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitChat();
        }
      });

      wrapper.appendChild(inp);
      wrapper.appendChild(btn);
      return wrapper;
    }

    if (type === 'text_input') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const label = document.createElement('label');
        label.className = 'pv-label';
        label.htmlFor = id;
        label.textContent = props.label;
        group.appendChild(label);
      }

      const input = document.createElement('input');
      input.className = 'pv-input';
      input.id = id;
      input.setAttribute('data-widget-id', id);
      input.type = props.input_type || 'text';
      input.value = props.value || '';
      input.placeholder = props.placeholder || '';

      lastWidgetValues.set(id, input.value);

      const dispatchChangeIfNeeded = () => {
        const currentVal = input.value;
        const previousVal = lastWidgetValues.get(id);
        if (currentVal !== previousVal) {
          lastWidgetValues.set(id, currentVal);
          sendWidgetEvent(id, currentVal, props.form_id);
        }
      };

      input.addEventListener('change', dispatchChangeIfNeeded);
      input.addEventListener('blur', dispatchChangeIfNeeded);
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') input.blur();
      });

      group.appendChild(input);
      return group;
    }

    if (type === 'text_area') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const label = document.createElement('label');
        label.className = 'pv-label';
        label.htmlFor = id;
        label.textContent = props.label;
        group.appendChild(label);
      }

      const textarea = document.createElement('textarea');
      textarea.className = 'pv-textarea';
      textarea.id = id;
      textarea.setAttribute('data-widget-id', id);
      textarea.value = props.value || '';
      textarea.placeholder = props.placeholder || '';
      if (props.height) {
        textarea.style.height = `${props.height}px`;
      }

      lastWidgetValues.set(id, textarea.value);

      const dispatchChangeIfNeeded = () => {
        const currentVal = textarea.value;
        const previousVal = lastWidgetValues.get(id);
        if (currentVal !== previousVal) {
          lastWidgetValues.set(id, currentVal);
          sendWidgetEvent(id, currentVal, props.form_id);
        }
      };

      textarea.addEventListener('change', dispatchChangeIfNeeded);
      textarea.addEventListener('blur', dispatchChangeIfNeeded);

      group.appendChild(textarea);
      return group;
    }

    if (type === 'checkbox') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      const container = document.createElement('label');
      container.className = 'pv-checkbox-container';

      const checkbox = document.createElement('input');
      checkbox.className = 'pv-checkbox-input';
      checkbox.type = 'checkbox';
      checkbox.id = id;
      checkbox.setAttribute('data-widget-id', id);
      checkbox.checked = Boolean(props.value);

      lastWidgetValues.set(id, checkbox.checked);

      checkbox.addEventListener('change', () => {
        lastWidgetValues.set(id, checkbox.checked);
        sendWidgetEvent(id, checkbox.checked, props.form_id);
      });

      const labelSpan = document.createElement('span');
      labelSpan.className = 'pv-checkbox-label';
      labelSpan.textContent = props.label || '';

      container.appendChild(checkbox);
      container.appendChild(labelSpan);
      group.appendChild(container);
      return group;
    }

    if (type === 'toggle') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      const wrapper = document.createElement('label');
      wrapper.className = 'pv-toggle-wrapper';

      let isChecked = Boolean(props.value);
      lastWidgetValues.set(id, isChecked);

      const sw = document.createElement('div');
      sw.className = `pv-toggle-switch ${isChecked ? 'pv-toggle-checked' : ''}`;

      const knob = document.createElement('div');
      knob.className = 'pv-toggle-knob';
      sw.appendChild(knob);

      const labelSpan = document.createElement('span');
      labelSpan.className = 'pv-toggle-label';
      labelSpan.textContent = props.label || '';

      wrapper.addEventListener('click', (e) => {
        e.preventDefault();
        isChecked = !isChecked;
        sw.className = `pv-toggle-switch ${isChecked ? 'pv-toggle-checked' : ''}`;
        lastWidgetValues.set(id, isChecked);
        sendWidgetEvent(id, isChecked, props.form_id);
      });

      wrapper.appendChild(sw);
      wrapper.appendChild(labelSpan);
      group.appendChild(wrapper);
      return group;
    }

    if (type === 'radio') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const radioGrp = document.createElement('div');
      radioGrp.className = `pv-radio-group ${props.horizontal ? 'pv-radio-horizontal' : ''}`;
      let selectedIdx = props.selected_index || 0;
      lastWidgetValues.set(id, selectedIdx);

      (props.options || []).forEach((optText, idx) => {
        const item = document.createElement('div');
        item.className = `pv-radio-item ${idx === selectedIdx ? 'pv-radio-selected' : ''}`;

        const circle = document.createElement('div');
        circle.className = 'pv-radio-circle';
        const dot = document.createElement('div');
        dot.className = 'pv-radio-dot';
        circle.appendChild(dot);

        const textSpan = document.createElement('span');
        textSpan.textContent = optText;

        item.appendChild(circle);
        item.appendChild(textSpan);

        item.addEventListener('click', () => {
          selectedIdx = idx;
          radioGrp.querySelectorAll('.pv-radio-item').forEach((el, i) => {
            if (i === idx) el.classList.add('pv-radio-selected');
            else el.classList.remove('pv-radio-selected');
          });
          lastWidgetValues.set(id, idx);
          sendWidgetEvent(id, idx, props.form_id);
        });

        radioGrp.appendChild(item);
      });

      group.appendChild(radioGrp);
      return group;
    }

    if (type === 'multiselect') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const container = document.createElement('div');
      container.className = 'pv-multiselect-container';

      const box = document.createElement('div');
      box.className = 'pv-ms-box';

      const dropdown = document.createElement('div');
      dropdown.className = 'pv-ms-dropdown';

      let currentIndices = [...(props.selected_indices || [])];
      lastWidgetValues.set(id, currentIndices);

      const renderMultiselectTags = () => {
        box.innerHTML = '';
        if (currentIndices.length === 0) {
          const ph = document.createElement('span');
          ph.className = 'pv-ms-placeholder';
          ph.textContent = props.placeholder || 'Choose options...';
          box.appendChild(ph);
        } else {
          currentIndices.forEach((idx) => {
            const tag = document.createElement('span');
            tag.className = 'pv-ms-tag';
            tag.textContent = (props.options && props.options[idx]) || String(idx);

            const rem = document.createElement('span');
            rem.className = 'pv-ms-tag-remove';
            rem.textContent = ' ✕';
            rem.addEventListener('click', (e) => {
              e.stopPropagation();
              currentIndices = currentIndices.filter((i) => i !== idx);
              renderMultiselectTags();
              renderDropdownOptions();
              lastWidgetValues.set(id, currentIndices);
              sendWidgetEvent(id, currentIndices, props.form_id);
            });

            tag.appendChild(rem);
            box.appendChild(tag);
          });
        }
      };

      const renderDropdownOptions = () => {
        dropdown.innerHTML = '';
        (props.options || []).forEach((optText, idx) => {
          const opt = document.createElement('div');
          const isSel = currentIndices.includes(idx);
          opt.className = `pv-ms-option ${isSel ? 'pv-ms-opt-selected' : ''}`;
          opt.textContent = optText;

          if (isSel) {
            const check = document.createElement('span');
            check.textContent = '✓';
            opt.appendChild(check);
          }

          opt.addEventListener('click', (e) => {
            e.stopPropagation();
            if (isSel) {
              currentIndices = currentIndices.filter((i) => i !== idx);
            } else {
              if (props.max_selections && currentIndices.length >= props.max_selections) return;
              currentIndices.push(idx);
            }
            renderMultiselectTags();
            renderDropdownOptions();
            lastWidgetValues.set(id, currentIndices);
            sendWidgetEvent(id, currentIndices, props.form_id);
          });

          dropdown.appendChild(opt);
        });
      };

      box.addEventListener('click', () => {
        dropdown.classList.toggle('pv-ms-open');
      });

      document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
          dropdown.classList.remove('pv-ms-open');
        }
      });

      renderMultiselectTags();
      renderDropdownOptions();
      container.appendChild(box);
      container.appendChild(dropdown);
      group.appendChild(container);
      return group;
    }

    if (type === 'color_picker') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const wrapper = document.createElement('div');
      wrapper.className = 'pv-color-picker-wrapper';

      const swatch = document.createElement('div');
      swatch.className = 'pv-color-swatch-box';
      swatch.style.backgroundColor = props.value || '#388bfd';

      const colorInp = document.createElement('input');
      colorInp.type = 'color';
      colorInp.className = 'pv-color-native-input';
      colorInp.setAttribute('data-widget-id', id);
      colorInp.value = props.value || '#388bfd';
      swatch.appendChild(colorInp);

      const hexLabel = document.createElement('span');
      hexLabel.className = 'pv-color-hex-label';
      hexLabel.textContent = props.value || '#388bfd';

      colorInp.addEventListener('input', () => {
        swatch.style.backgroundColor = colorInp.value;
        hexLabel.textContent = colorInp.value;
      });

      colorInp.addEventListener('change', () => {
        lastWidgetValues.set(id, colorInp.value);
        sendWidgetEvent(id, colorInp.value, props.form_id);
      });

      wrapper.appendChild(swatch);
      wrapper.appendChild(hexLabel);
      group.appendChild(wrapper);
      return group;
    }

    if (type === 'feedback') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      const container = document.createElement('div');
      container.className = 'pv-feedback-container';
      const feedbackType = props.feedback_type || 'stars';
      const currentVal = props.value;

      if (feedbackType === 'stars') {
        for (let k = 1; k <= 5; k++) {
          const btn = document.createElement('button');
          btn.className = `pv-feedback-btn ${currentVal !== null && currentVal >= k ? 'pv-feedback-active' : ''}`;
          btn.textContent = '⭐';
          btn.title = `${k} Star${k > 1 ? 's' : ''}`;
          btn.addEventListener('click', (e) => {
            e.preventDefault();
            sendWidgetEvent(id, k, props.form_id);
          });
          container.appendChild(btn);
        }
      } else if (feedbackType === 'thumbs') {
        const btnUp = document.createElement('button');
        btnUp.className = `pv-feedback-btn ${currentVal === 1 ? 'pv-feedback-active' : ''}`;
        btnUp.textContent = '👍';
        btnUp.addEventListener('click', (e) => {
          e.preventDefault();
          sendWidgetEvent(id, 1, props.form_id);
        });

        const btnDown = document.createElement('button');
        btnDown.className = `pv-feedback-btn ${currentVal === 0 ? 'pv-feedback-active' : ''}`;
        btnDown.textContent = '👎';
        btnDown.addEventListener('click', (e) => {
          e.preventDefault();
          sendWidgetEvent(id, 0, props.form_id);
        });

        container.appendChild(btnUp);
        container.appendChild(btnDown);
      } else if (feedbackType === 'faces') {
        const faces = ['😡', '🙁', '😐', '🙂', '😄'];
        faces.forEach((emoji, idx) => {
          const btn = document.createElement('button');
          btn.className = `pv-feedback-btn ${currentVal === idx + 1 ? 'pv-feedback-active' : ''}`;
          btn.textContent = emoji;
          btn.addEventListener('click', (e) => {
            e.preventDefault();
            sendWidgetEvent(id, idx + 1, props.form_id);
          });
          container.appendChild(btn);
        });
      }

      group.appendChild(container);
      return group;
    }

    if (type === 'segmented_control') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const ctrl = document.createElement('div');
      ctrl.className = 'pv-segmented-control';
      const isMulti = props.selection_mode === 'multi';

      (props.options || []).forEach((optText) => {
        const btn = document.createElement('button');
        const isSel = isMulti
          ? Array.isArray(props.selected) && props.selected.includes(optText)
          : props.selected === optText;
        btn.className = `pv-segment-btn ${isSel ? 'pv-segment-active' : ''}`;
        btn.textContent = optText;

        btn.addEventListener('click', (e) => {
          e.preventDefault();
          if (isMulti) {
            let list = Array.isArray(props.selected) ? [...props.selected] : [];
            if (list.includes(optText)) list = list.filter((x) => x !== optText);
            else list.push(optText);
            sendWidgetEvent(id, list, props.form_id);
          } else {
            sendWidgetEvent(id, optText, props.form_id);
          }
        });

        ctrl.appendChild(btn);
      });

      group.appendChild(ctrl);
      return group;
    }

    if (type === 'select_slider') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const wrapper = document.createElement('div');
      wrapper.className = 'pv-select-slider-wrapper';

      const sliderInp = document.createElement('input');
      sliderInp.type = 'range';
      sliderInp.className = 'pv-slider-input';
      sliderInp.setAttribute('data-widget-id', id);
      const opts = props.options || [];
      sliderInp.min = 0;
      sliderInp.max = Math.max(0, opts.length - 1);
      sliderInp.step = 1;
      sliderInp.value = props.selected_index || 0;

      const tickRow = document.createElement('div');
      tickRow.className = 'pv-slider-ticks';
      opts.forEach((o) => {
        const sp = document.createElement('span');
        sp.textContent = o;
        tickRow.appendChild(sp);
      });

      sliderInp.addEventListener('change', () => {
        sendWidgetEvent(id, parseInt(sliderInp.value, 10), props.form_id);
      });

      wrapper.appendChild(sliderInp);
      wrapper.appendChild(tickRow);
      group.appendChild(wrapper);
      return group;
    }

    if (type === 'date_input') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const container = document.createElement('div');
      container.className = 'pv-custom-picker-container';

      // Parse initial value (YYYY-MM-DD)
      let selectedDate = props.value ? new Date(props.value + 'T00:00:00') : new Date();
      if (isNaN(selectedDate.getTime())) selectedDate = new Date();

      let viewYear = selectedDate.getFullYear();
      let viewMonth = selectedDate.getMonth(); // 0-11

      const triggerBtn = document.createElement('button');
      triggerBtn.type = 'button';
      triggerBtn.className = 'pv-custom-picker-btn';
      triggerBtn.setAttribute('data-widget-id', id);

      const displayVal = document.createElement('span');
      displayVal.className = 'pv-picker-display-val';

      const icon = document.createElement('span');
      icon.className = 'pv-picker-icon';
      icon.textContent = '📅';

      const textSpan = document.createElement('span');

      const formatDisplay = (d) => {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${months[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
      };

      const formatIso = (d) => {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
      };

      textSpan.textContent = formatDisplay(selectedDate);
      displayVal.appendChild(icon);
      displayVal.appendChild(textSpan);

      const chevron = document.createElement('span');
      chevron.style.fontSize = '10px';
      chevron.style.color = 'var(--text-muted)';
      chevron.textContent = '▼';

      triggerBtn.appendChild(displayVal);
      triggerBtn.appendChild(chevron);

      // Popover
      const popover = document.createElement('div');
      popover.className = 'pv-picker-popover';

      const renderCalendar = () => {
        popover.innerHTML = '';

        // Header
        const header = document.createElement('div');
        header.className = 'pv-cal-header';

        const prevBtn = document.createElement('button');
        prevBtn.type = 'button';
        prevBtn.className = 'pv-cal-nav-btn';
        prevBtn.textContent = '◀';
        prevBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          viewMonth--;
          if (viewMonth < 0) {
            viewMonth = 11;
            viewYear--;
          }
          renderCalendar();
        });

        const title = document.createElement('div');
        title.className = 'pv-cal-title';
        const monthNames = [
          'January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December'
        ];
        title.textContent = `${monthNames[viewMonth]} ${viewYear}`;

        const nextBtn = document.createElement('button');
        nextBtn.type = 'button';
        nextBtn.className = 'pv-cal-nav-btn';
        nextBtn.textContent = '▶';
        nextBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          viewMonth++;
          if (viewMonth > 11) {
            viewMonth = 0;
            viewYear++;
          }
          renderCalendar();
        });

        header.appendChild(prevBtn);
        header.appendChild(title);
        header.appendChild(nextBtn);
        popover.appendChild(header);

        // Weekday labels
        const weekdays = document.createElement('div');
        weekdays.className = 'pv-cal-weekdays';
        ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'].forEach((dayName) => {
          const w = document.createElement('span');
          w.textContent = dayName;
          weekdays.appendChild(w);
        });
        popover.appendChild(weekdays);

        // Days Grid
        const daysGrid = document.createElement('div');
        daysGrid.className = 'pv-cal-days-grid';

        const firstDayOfMonth = new Date(viewYear, viewMonth, 1);
        let startDay = firstDayOfMonth.getDay() - 1;
        if (startDay === -1) startDay = 6;

        const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
        const daysInPrevMonth = new Date(viewYear, viewMonth, 0).getDate();

        const today = new Date();
        const todayIso = formatIso(today);
        const selIso = formatIso(selectedDate);

        // Previous month days
        for (let i = startDay - 1; i >= 0; i--) {
          const cell = document.createElement('div');
          cell.className = 'pv-cal-day-cell pv-cal-other-month';
          cell.textContent = daysInPrevMonth - i;
          daysGrid.appendChild(cell);
        }

        // Current month days
        for (let d = 1; d <= daysInMonth; d++) {
          const cell = document.createElement('div');
          cell.className = 'pv-cal-day-cell';
          cell.textContent = d;

          const thisDate = new Date(viewYear, viewMonth, d);
          const thisIso = formatIso(thisDate);

          if (thisIso === todayIso) {
            cell.classList.add('pv-cal-today');
          }
          if (thisIso === selIso) {
            cell.classList.add('pv-cal-selected');
          }

          if (props.min_value && thisIso < props.min_value) {
            cell.classList.add('pv-cal-disabled');
          } else if (props.max_value && thisIso > props.max_value) {
            cell.classList.add('pv-cal-disabled');
          } else {
            cell.addEventListener('click', (e) => {
              e.stopPropagation();
              selectedDate = thisDate;
              textSpan.textContent = formatDisplay(selectedDate);
              popover.classList.remove('pv-picker-open');
              triggerBtn.classList.remove('pv-picker-active');
              lastWidgetValues.set(id, thisIso);
              sendWidgetEvent(id, thisIso, props.form_id);
            });
          }

          daysGrid.appendChild(cell);
        }

        // Remaining days
        const totalCells = startDay + daysInMonth;
        const nextDays = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
        for (let n = 1; n <= nextDays; n++) {
          const cell = document.createElement('div');
          cell.className = 'pv-cal-day-cell pv-cal-other-month';
          cell.textContent = n;
          daysGrid.appendChild(cell);
        }

        popover.appendChild(daysGrid);

        // Footer Actions
        const footer = document.createElement('div');
        footer.className = 'pv-cal-footer';

        const btnToday = document.createElement('button');
        btnToday.type = 'button';
        btnToday.className = 'pv-cal-action-btn';
        btnToday.textContent = 'Today';
        btnToday.addEventListener('click', (e) => {
          e.stopPropagation();
          selectedDate = new Date();
          viewYear = selectedDate.getFullYear();
          viewMonth = selectedDate.getMonth();
          textSpan.textContent = formatDisplay(selectedDate);
          popover.classList.remove('pv-picker-open');
          triggerBtn.classList.remove('pv-picker-active');
          const todayIsoStr = formatIso(selectedDate);
          lastWidgetValues.set(id, todayIsoStr);
          sendWidgetEvent(id, todayIsoStr, props.form_id);
        });

        footer.appendChild(btnToday);
        popover.appendChild(footer);
      };

      triggerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popover.classList.contains('pv-picker-open');
        document.querySelectorAll('.pv-picker-popover').forEach((p) => p.classList.remove('pv-picker-open'));
        document.querySelectorAll('.pv-custom-picker-btn').forEach((b) => b.classList.remove('pv-picker-active'));

        if (!isOpen) {
          viewYear = selectedDate.getFullYear();
          viewMonth = selectedDate.getMonth();
          renderCalendar();
          popover.classList.add('pv-picker-open');
          triggerBtn.classList.add('pv-picker-active');
        }
      });

      document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
          popover.classList.remove('pv-picker-open');
          triggerBtn.classList.remove('pv-picker-active');
        }
      });

      container.appendChild(triggerBtn);
      container.appendChild(popover);
      group.appendChild(container);
      return group;
    }

    if (type === 'time_input') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const container = document.createElement('div');
      container.className = 'pv-custom-picker-container';

      // Parse initial value (HH:MM or HH:MM:SS)
      let rawVal = props.value || '09:00:00';
      let parts = rawVal.split(':');
      let h24 = parseInt(parts[0], 10);
      if (isNaN(h24)) h24 = 9;
      let minute = parseInt(parts[1], 10);
      if (isNaN(minute)) minute = 0;

      let isPm = h24 >= 12;
      let hour12 = h24 % 12;
      if (hour12 === 0) hour12 = 12;

      let currentMode = 'hour'; // 'hour' | 'minute'

      const triggerBtn = document.createElement('button');
      triggerBtn.type = 'button';
      triggerBtn.className = 'pv-custom-picker-btn';
      triggerBtn.setAttribute('data-widget-id', id);

      const displayVal = document.createElement('span');
      displayVal.className = 'pv-picker-display-val';

      const icon = document.createElement('span');
      icon.className = 'pv-picker-icon';
      icon.textContent = '🕒';

      const textSpan = document.createElement('span');

      const getIsoTime = () => {
        let finalH = hour12 % 12;
        if (isPm) finalH += 12;
        const strH = String(finalH).padStart(2, '0');
        const strM = String(minute).padStart(2, '0');
        return `${strH}:${strM}:00`;
      };

      const getDisplayTime = () => {
        let finalH = hour12 % 12;
        if (isPm) finalH += 12;
        const strH = String(finalH).padStart(2, '0');
        const strM = String(minute).padStart(2, '0');
        return `${strH}:${strM}`;
      };

      textSpan.textContent = getDisplayTime();
      displayVal.appendChild(icon);
      displayVal.appendChild(textSpan);

      const chevron = document.createElement('span');
      chevron.style.fontSize = '10px';
      chevron.style.color = 'var(--text-muted)';
      chevron.textContent = '▼';

      triggerBtn.appendChild(displayVal);
      triggerBtn.appendChild(chevron);

      // Popover
      const popover = document.createElement('div');
      popover.className = 'pv-picker-popover pv-time-popover';

      const commitChange = () => {
        textSpan.textContent = getDisplayTime();
        const iso = getIsoTime();
        lastWidgetValues.set(id, iso);
        sendWidgetEvent(id, iso, props.form_id);
      };

      const renderClock = () => {
        popover.innerHTML = '';

        // 1. Digital Display Header
        const header = document.createElement('div');
        header.className = 'pv-clock-header';

        const digitalDisplay = document.createElement('div');
        digitalDisplay.className = 'pv-clock-digital-display';

        const hourBtn = document.createElement('button');
        hourBtn.type = 'button';
        hourBtn.className = `pv-clock-digit-btn ${currentMode === 'hour' ? 'pv-clock-digit-active' : ''}`;
        hourBtn.textContent = String(hour12).padStart(2, '0');
        hourBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          currentMode = 'hour';
          renderClock();
        });

        const colon = document.createElement('span');
        colon.className = 'pv-clock-digital-colon';
        colon.textContent = ':';

        const minuteBtn = document.createElement('button');
        minuteBtn.type = 'button';
        minuteBtn.className = `pv-clock-digit-btn ${currentMode === 'minute' ? 'pv-clock-digit-active' : ''}`;
        minuteBtn.textContent = String(minute).padStart(2, '0');
        minuteBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          currentMode = 'minute';
          renderClock();
        });

        digitalDisplay.appendChild(hourBtn);
        digitalDisplay.appendChild(colon);
        digitalDisplay.appendChild(minuteBtn);

        // AM/PM Toggle
        const ampmGroup = document.createElement('div');
        ampmGroup.className = 'pv-clock-ampm-group';

        const amBtn = document.createElement('button');
        amBtn.type = 'button';
        amBtn.className = `pv-clock-ampm-btn ${!isPm ? 'pv-ampm-active' : ''}`;
        amBtn.textContent = 'AM';
        amBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          isPm = false;
          commitChange();
          renderClock();
        });

        const pmBtn = document.createElement('button');
        pmBtn.type = 'button';
        pmBtn.className = `pv-clock-ampm-btn ${isPm ? 'pv-ampm-active' : ''}`;
        pmBtn.textContent = 'PM';
        pmBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          isPm = true;
          commitChange();
          renderClock();
        });

        ampmGroup.appendChild(amBtn);
        ampmGroup.appendChild(pmBtn);

        header.appendChild(digitalDisplay);
        header.appendChild(ampmGroup);
        popover.appendChild(header);

        // 2. Circular Clock Face Dial
        const dial = document.createElement('div');
        dial.className = 'pv-clock-dial';

        // Center dot
        const dot = document.createElement('div');
        dot.className = 'pv-clock-center-dot';
        dial.appendChild(dot);

        // Hand
        const hand = document.createElement('div');
        hand.className = 'pv-clock-hand';
        const knob = document.createElement('div');
        knob.className = 'pv-clock-hand-knob';
        const innerDot = document.createElement('div');
        innerDot.className = 'pv-clock-hand-inner-dot';
        knob.appendChild(innerDot);
        hand.appendChild(knob);

        // Compute angle for hand
        let currentAngle = 0;
        if (currentMode === 'hour') {
          currentAngle = (hour12 % 12) * 30;
        } else {
          currentAngle = minute * 6;
        }
        hand.style.transform = `rotate(${currentAngle}deg)`;
        dial.appendChild(hand);

        // Render Numbers on Dial
        const dialCenter = 110;
        const radius = 80;

        if (currentMode === 'hour') {
          for (let h = 1; h <= 12; h++) {
            const numEl = document.createElement('div');
            numEl.className = `pv-clock-number ${h === hour12 ? 'pv-clock-num-selected' : ''}`;
            numEl.textContent = h;

            const deg = h * 30;
            const rad = (deg * Math.PI) / 180;
            const x = dialCenter + radius * Math.sin(rad) - 16;
            const y = dialCenter - radius * Math.cos(rad) - 16;

            numEl.style.left = `${x}px`;
            numEl.style.top = `${y}px`;
            dial.appendChild(numEl);
          }
        } else {
          for (let m = 0; m < 60; m += 5) {
            const numEl = document.createElement('div');
            numEl.className = `pv-clock-number ${m === minute ? 'pv-clock-num-selected' : ''}`;
            numEl.textContent = String(m).padStart(2, '0');

            const deg = m * 6;
            const rad = (deg * Math.PI) / 180;
            const x = dialCenter + radius * Math.sin(rad) - 16;
            const y = dialCenter - radius * Math.cos(rad) - 16;

            numEl.style.left = `${x}px`;
            numEl.style.top = `${y}px`;
            dial.appendChild(numEl);
          }
        }

        // Handle Dial Interaction (Click or Drag)
        const updateFromPointer = (e, isFinal) => {
          const rect = dial.getBoundingClientRect();
          const clientX = e.touches ? e.touches[0].clientX : e.clientX;
          const clientY = e.touches ? e.touches[0].clientY : e.clientY;

          const dx = clientX - (rect.left + rect.width / 2);
          const dy = clientY - (rect.top + rect.height / 2);

          let rad = Math.atan2(dx, -dy);
          let deg = (rad * 180) / Math.PI;
          if (deg < 0) deg += 360;

          if (currentMode === 'hour') {
            let h = Math.round(deg / 30) % 12;
            if (h === 0) h = 12;
            hour12 = h;
            commitChange();
            if (isFinal) {
              setTimeout(() => {
                currentMode = 'minute';
                renderClock();
              }, 200);
            } else {
              renderClock();
            }
          } else {
            let m = Math.round(deg / 6) % 60;
            minute = m;
            commitChange();
            renderClock();
          }
        };

        dial.addEventListener('click', (e) => {
          e.stopPropagation();
          updateFromPointer(e, true);
        });

        popover.appendChild(dial);

        // 3. Footer Actions
        const footer = document.createElement('div');
        footer.className = 'pv-clock-footer';

        const btnNow = document.createElement('button');
        btnNow.type = 'button';
        btnNow.className = 'pv-cal-action-btn';
        btnNow.textContent = 'Now';
        btnNow.addEventListener('click', (e) => {
          e.stopPropagation();
          const now = new Date();
          let nowH = now.getHours();
          minute = now.getMinutes();
          isPm = nowH >= 12;
          hour12 = nowH % 12;
          if (hour12 === 0) hour12 = 12;
          commitChange();
          renderClock();
        });

        const btnDone = document.createElement('button');
        btnDone.type = 'button';
        btnDone.className = 'pv-cal-action-btn';
        btnDone.style.color = 'var(--accent-primary)';
        btnDone.textContent = 'Done';
        btnDone.addEventListener('click', (e) => {
          e.stopPropagation();
          popover.classList.remove('pv-picker-open');
          triggerBtn.classList.remove('pv-picker-active');
        });

        footer.appendChild(btnNow);
        footer.appendChild(btnDone);
        popover.appendChild(footer);
      };

      triggerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popover.classList.contains('pv-picker-open');
        document.querySelectorAll('.pv-picker-popover').forEach((p) => p.classList.remove('pv-picker-open'));
        document.querySelectorAll('.pv-custom-picker-btn').forEach((b) => b.classList.remove('pv-picker-active'));

        if (!isOpen) {
          currentMode = 'hour';
          renderClock();
          popover.classList.add('pv-picker-open');
          triggerBtn.classList.add('pv-picker-active');
        }
      });

      document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
          popover.classList.remove('pv-picker-open');
          triggerBtn.classList.remove('pv-picker-active');
        }
      });

      container.appendChild(triggerBtn);
      container.appendChild(popover);
      group.appendChild(container);
      return group;
    }

    if (type === 'file_uploader') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const lbl = document.createElement('label');
        lbl.className = 'pv-label';
        lbl.textContent = props.label;
        group.appendChild(lbl);
      }

      const box = document.createElement('div');
      box.className = 'pv-file-uploader-box';

      const icon = document.createElement('div');
      icon.className = 'pv-uploader-icon';
      icon.textContent = '☁️';

      const title = document.createElement('div');
      title.className = 'pv-uploader-label';
      title.textContent = 'Drag and drop files here, or click to browse';

      const hint = document.createElement('div');
      hint.className = 'pv-uploader-hint';
      const allowed = props.allowed_types && props.allowed_types.length ? `Limit: ${props.allowed_types.join(', ')}` : 'All file types supported';
      hint.textContent = allowed;

      const fileInp = document.createElement('input');
      fileInp.type = 'file';
      fileInp.style.display = 'none';
      if (props.allowed_types && props.allowed_types.length) {
        fileInp.accept = props.allowed_types.map((t) => (t.startsWith('.') ? t : `.${t}`)).join(',');
      }

      const handleFileUpload = (file) => {
        const sessId = sessionStorage.getItem('pyview_session_id') || 'sess_default';
        const formData = new FormData();
        formData.append('file', file);
        fetch(`/_pyview/upload/${sessId}/${id}`, { method: 'POST', body: formData })
          .then((r) => r.json())
          .then((res) => {
            sendMessage({ type: 'widget_event', key: id, value: res.name, is_trigger: true });
          })
          .catch((err) => console.error('File upload failed:', err));
      };

      box.appendChild(icon);
      box.appendChild(title);
      box.appendChild(hint);
      box.appendChild(fileInp);

      box.addEventListener('click', () => fileInp.click());
      box.addEventListener('dragover', (e) => {
        e.preventDefault();
        box.classList.add('pv-uploader-dragover');
      });
      box.addEventListener('dragleave', () => box.classList.remove('pv-uploader-dragover'));
      box.addEventListener('drop', (e) => {
        e.preventDefault();
        box.classList.remove('pv-uploader-dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length) {
          handleFileUpload(e.dataTransfer.files[0]);
        }
      });
      fileInp.addEventListener('change', () => {
        if (fileInp.files && fileInp.files.length) {
          handleFileUpload(fileInp.files[0]);
        }
      });

      if (props.has_file && props.file_name) {
        const card = document.createElement('div');
        card.className = 'pv-uploader-file-card';
        card.innerHTML = `<span>📄 <strong>${props.file_name}</strong> (${Math.round((props.file_size || 0) / 1024)} KB)</span><span style="color: var(--success-color);">✅ Uploaded</span>`;
        group.appendChild(box);
        group.appendChild(card);
      } else {
        group.appendChild(box);
      }

      return group;
    }

    if (type === 'slider') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const label = document.createElement('label');
        label.className = 'pv-label';
        label.htmlFor = id;
        label.textContent = props.label;
        group.appendChild(label);
      }

      const wrapper = document.createElement('div');
      wrapper.className = 'pv-slider-wrapper';

      const sliderInput = document.createElement('input');
      sliderInput.className = 'pv-slider-input';
      sliderInput.type = 'range';
      sliderInput.id = id;
      sliderInput.setAttribute('data-widget-id', id);
      sliderInput.min = props.min_value !== undefined ? props.min_value : 0;
      sliderInput.max = props.max_value !== undefined ? props.max_value : 100;
      sliderInput.step = props.step !== undefined ? props.step : 1;
      sliderInput.value = props.value !== undefined ? props.value : props.min_value;

      const valueBubble = document.createElement('span');
      valueBubble.className = 'pv-slider-value';
      valueBubble.textContent = sliderInput.value;

      sliderInput.addEventListener('input', () => {
        valueBubble.textContent = sliderInput.value;
      });

      sliderInput.addEventListener('change', () => {
        const parsed = props.is_float ? parseFloat(sliderInput.value) : parseInt(sliderInput.value, 10);
        lastWidgetValues.set(id, parsed);
        sendWidgetEvent(id, parsed, props.form_id);
      });

      wrapper.appendChild(sliderInput);
      wrapper.appendChild(valueBubble);
      group.appendChild(wrapper);
      return group;
    }

    if (type === 'number_input') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const label = document.createElement('label');
        label.className = 'pv-label';
        label.htmlFor = id;
        label.textContent = props.label;
        group.appendChild(label);
      }

      const input = document.createElement('input');
      input.className = 'pv-input';
      input.type = 'number';
      input.id = id;
      input.setAttribute('data-widget-id', id);
      if (props.min_value !== undefined && props.min_value !== null) input.min = props.min_value;
      if (props.max_value !== undefined && props.max_value !== null) input.max = props.max_value;
      if (props.step !== undefined && props.step !== null) input.step = props.step;
      input.value = props.value !== undefined ? props.value : 0;

      lastWidgetValues.set(id, input.value);

      const dispatchChangeIfNeeded = () => {
        const currentVal = input.value;
        const previousVal = lastWidgetValues.get(id);
        if (currentVal !== previousVal) {
          lastWidgetValues.set(id, currentVal);
          const parsed = props.is_float ? parseFloat(currentVal) : parseInt(currentVal, 10);
          sendWidgetEvent(id, isNaN(parsed) ? 0 : parsed, props.form_id);
        }
      };

      input.addEventListener('change', dispatchChangeIfNeeded);
      input.addEventListener('blur', dispatchChangeIfNeeded);
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') input.blur();
      });

      group.appendChild(input);
      return group;
    }

    if (type === 'selectbox') {
      const group = document.createElement('div');
      group.className = 'pv-form-group';
      group.id = `group-${id}`;

      if (props.label) {
        const label = document.createElement('label');
        label.className = 'pv-label';
        label.htmlFor = id;
        label.textContent = props.label;
        group.appendChild(label);
      }

      const select = document.createElement('select');
      select.className = 'pv-select';
      select.id = id;
      select.setAttribute('data-widget-id', id);

      const options = props.options || [];
      const selectedIndex = props.selected_index || 0;

      options.forEach((optText, idx) => {
        const opt = document.createElement('option');
        opt.value = idx;
        opt.textContent = optText;
        if (idx === selectedIndex) {
          opt.selected = true;
        }
        select.appendChild(opt);
      });

      select.addEventListener('change', () => {
        const chosenIndex = parseInt(select.selectedIndex, 10);
        lastWidgetValues.set(id, chosenIndex);
        sendWidgetEvent(id, chosenIndex, props.form_id);
      });

      group.appendChild(select);
      return group;
    }


    if (type === 'alert') {
      const alertDiv = document.createElement('div');
      alertDiv.className = `pv-alert pv-alert-${props.alert_type || 'info'}`;
      alertDiv.id = id;

      const iconSpan = document.createElement('span');
      iconSpan.className = 'pv-alert-icon';
      iconSpan.textContent = props.icon || 'ℹ️';

      const textSpan = document.createElement('div');
      textSpan.className = 'pv-alert-text';
      textSpan.innerHTML = formatTextContent(props.text || '');

      alertDiv.appendChild(iconSpan);
      alertDiv.appendChild(textSpan);
      return alertDiv;
    }

    if (type === 'metric') {
      const card = document.createElement('div');
      card.className = 'pv-metric-card';
      card.id = id;

      const label = document.createElement('div');
      label.className = 'pv-metric-label';
      label.textContent = props.label || '';

      const value = document.createElement('div');
      value.className = 'pv-metric-value';
      value.textContent = props.value || '';

      card.appendChild(label);
      card.appendChild(value);

      if (props.delta) {
        const deltaEl = document.createElement('div');
        deltaEl.className = 'pv-metric-delta';

        const deltaColor = props.delta_color || 'normal';
        const dir = props.delta_direction || 'neutral';

        let colorClass = 'pv-delta-neutral';
        let arrow = '';

        if (deltaColor === 'normal') {
          if (dir === 'positive') {
            colorClass = 'pv-delta-positive';
            arrow = '▲ ';
          } else if (dir === 'negative') {
            colorClass = 'pv-delta-negative';
            arrow = '▼ ';
          }
        } else if (deltaColor === 'inverse') {
          if (dir === 'positive') {
            colorClass = 'pv-delta-negative';
            arrow = '▲ ';
          } else if (dir === 'negative') {
            colorClass = 'pv-delta-positive';
            arrow = '▼ ';
          }
        }

        deltaEl.className = `pv-metric-delta ${colorClass}`;
        deltaEl.textContent = `${arrow}${props.delta}`;
        card.appendChild(deltaEl);
      }

      return card;
    }

    if (type === 'table') {
      const wrapper = document.createElement('div');
      wrapper.className = 'pv-table-wrapper';
      wrapper.id = id;

      const tbl = document.createElement('table');
      tbl.className = 'pv-table';

      const columns = props.columns || [];
      const rows = props.data || [];

      if (columns.length > 0) {
        const thead = document.createElement('thead');
        const tr = document.createElement('tr');
        columns.forEach((col) => {
          const th = document.createElement('th');
          th.textContent = col;
          tr.appendChild(th);
        });
        thead.appendChild(tr);
        tbl.appendChild(thead);
      }

      const tbody = document.createElement('tbody');
      rows.forEach((row) => {
        const tr = document.createElement('tr');
        row.forEach((cellVal) => {
          const td = document.createElement('td');
          td.textContent = cellVal !== null && cellVal !== undefined ? cellVal : '';
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      tbl.appendChild(tbody);
      wrapper.appendChild(tbl);
      return wrapper;
    }

    if (type === 'dataframe') {
      const container = document.createElement('div');
      container.className = 'pv-dataframe-container';
      container.id = id;

      const columns = props.columns || [];
      const initialRows = props.data || [];
      const columnConfig = props.column_config || {};

      let currentRows = [...initialRows];
      let sortColIdx = null;
      let sortAsc = true;
      let currentPage = 1;
      let pageSize = 10;
      let searchQuery = '';

      // Toolbar
      const toolbar = document.createElement('div');
      toolbar.className = 'pv-df-toolbar';

      const searchInput = document.createElement('input');
      searchInput.className = 'pv-df-search';
      searchInput.placeholder = `🔍 Search ${columns.length} columns...`;

      const actions = document.createElement('div');
      actions.className = 'pv-df-actions';

      const btnExport = document.createElement('button');
      btnExport.className = 'pv-df-btn';
      btnExport.textContent = '📥 Download CSV';
      btnExport.addEventListener('click', (e) => {
        e.preventDefault();
        const csvContent = [
          columns.join(','),
          ...currentRows.map((r) => r.map((c) => `"${String(c !== null ? c : '').replace(/"/g, '""')}"`).join(',')),
        ].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `export_${id}.csv`;
        link.click();
      });

      actions.appendChild(btnExport);
      toolbar.appendChild(searchInput);
      toolbar.appendChild(actions);

      // Table Wrapper
      const tableWrapper = document.createElement('div');
      tableWrapper.className = 'pv-df-table-wrapper';

      const table = document.createElement('table');
      table.className = 'pv-df-table';

      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');

      columns.forEach((colName, cIdx) => {
        const th = document.createElement('th');
        th.className = 'pv-df-th-sortable';
        th.textContent = (columnConfig[colName] && columnConfig[colName].label) || colName;

        const sortIcon = document.createElement('span');
        sortIcon.className = 'pv-df-sort-icon';
        sortIcon.textContent = ' ⇅';
        th.appendChild(sortIcon);

        th.addEventListener('click', () => {
          if (sortColIdx === cIdx) {
            sortAsc = !sortAsc;
          } else {
            sortColIdx = cIdx;
            sortAsc = true;
          }
          applyFilterAndSort();
          renderTableRows();
        });

        headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      table.appendChild(tbody);
      tableWrapper.appendChild(table);

      // Pagination
      const pagination = document.createElement('div');
      pagination.className = 'pv-df-pagination';

      const pageInfo = document.createElement('span');
      const pageControls = document.createElement('div');
      pageControls.className = 'pv-df-page-controls';

      const btnPrev = document.createElement('button');
      btnPrev.className = 'pv-df-btn';
      btnPrev.textContent = '◀ Prev';

      const btnNext = document.createElement('button');
      btnNext.className = 'pv-df-btn';
      btnNext.textContent = 'Next ▶';

      pageControls.appendChild(btnPrev);
      pageControls.appendChild(btnNext);
      pagination.appendChild(pageInfo);
      pagination.appendChild(pageControls);

      function applyFilterAndSort() {
        let filtered = searchQuery.trim()
          ? initialRows.filter((row) => {
              const q = searchQuery.toLowerCase();
              return row.some((cell) => cell !== null && cell !== undefined && String(cell).toLowerCase().includes(q));
            })
          : [...initialRows];

        if (sortColIdx !== null) {
          filtered.sort((a, b) => {
            const vA = a[sortColIdx];
            const vB = b[sortColIdx];
            if (vA === vB) return 0;
            if (vA === null || vA === undefined) return 1;
            if (vB === null || vB === undefined) return -1;
            if (typeof vA === 'number' && typeof vB === 'number') {
              return sortAsc ? vA - vB : vB - vA;
            }
            const sA = String(vA).toLowerCase();
            const sB = String(vB).toLowerCase();
            return sortAsc ? (sA < sB ? -1 : (sA > sB ? 1 : 0)) : (sB < sA ? -1 : (sB > sA ? 1 : 0));
          });
        }

        currentRows = filtered;
        currentPage = 1;
      }

      function renderTableRows() {
        tbody.innerHTML = '';
        const totalRows = currentRows.length;
        const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
        if (currentPage > totalPages) currentPage = totalPages;

        const startIdx = (currentPage - 1) * pageSize;
        const pageRows = currentRows.slice(startIdx, startIdx + pageSize);

        pageRows.forEach((row) => {
          const tr = document.createElement('tr');
          row.forEach((cellVal, cIdx) => {
            const colName = columns[cIdx];
            const cfg = columnConfig[colName] || {};
            const td = document.createElement('td');

            if (cfg.type === 'progress') {
              const minVal = cfg.min_value !== undefined ? cfg.min_value : 0;
              const maxVal = cfg.max_value !== undefined ? cfg.max_value : 100;
              const num = typeof cellVal === 'number' ? cellVal : parseFloat(cellVal) || 0;
              const pct = Math.max(0, Math.min(100, ((num - minVal) / (maxVal - minVal)) * 100));

              const progCell = document.createElement('div');
              progCell.className = 'pv-progress-cell';

              const bar = document.createElement('div');
              bar.className = 'pv-progress-bar';
              const fill = document.createElement('div');
              fill.className = 'pv-progress-fill';
              fill.style.width = `${pct}%`;
              bar.appendChild(fill);

              const txt = document.createElement('span');
              txt.className = 'pv-progress-text';
              txt.textContent = `${Math.round(pct)}%`;

              progCell.appendChild(bar);
              progCell.appendChild(txt);
              td.appendChild(progCell);
            } else if (cfg.type === 'link') {
              const a = document.createElement('a');
              a.className = 'pv-link-cell';
              a.href = String(cellVal || '#');
              a.target = '_blank';
              a.rel = 'noopener noreferrer';
              a.textContent = cfg.display_text || String(cellVal || 'Link');
              td.appendChild(a);
            } else if (cfg.type === 'checkbox') {
              td.textContent = cellVal ? '✅' : '❌';
            } else if (cfg.type === 'number' && cfg.format && typeof cellVal === 'number') {
              if (cfg.format.startsWith('$')) {
                td.textContent = `$${cellVal.toLocaleString()}`;
              } else if (cfg.format.endsWith('%')) {
                td.textContent = `${cellVal}%`;
              } else {
                td.textContent = cellVal.toLocaleString();
              }
            } else {
              td.textContent = cellVal !== null && cellVal !== undefined ? cellVal : '';
            }

            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });

        pageInfo.textContent = `Showing ${Math.min(totalRows, startIdx + 1)}–${Math.min(totalRows, startIdx + pageSize)} of ${totalRows} rows`;
        btnPrev.disabled = currentPage <= 1;
        btnNext.disabled = currentPage >= totalPages;
      }

      let searchDebounceTimer = null;
      searchInput.addEventListener('input', () => {
        if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
          searchQuery = searchInput.value;
          applyFilterAndSort();
          renderTableRows();
        }, 150);
      });

      btnPrev.addEventListener('click', () => {
        if (currentPage > 1) {
          currentPage--;
          renderTableRows();
        }
      });

      btnNext.addEventListener('click', () => {
        const totalPages = Math.ceil(currentRows.length / pageSize);
        if (currentPage < totalPages) {
          currentPage++;
          renderTableRows();
        }
      });

      renderTableRows();

      container.appendChild(toolbar);
      container.appendChild(tableWrapper);
      container.appendChild(pagination);
      return container;
    }

    if (type === 'data_editor') {
      const container = document.createElement('div');
      container.className = 'pv-data-editor-container';
      container.id = id;

      const columns = props.columns || [];
      const rows = (props.data || []).map((r) => [...r]);
      const columnConfig = props.column_config || {};
      const isDynamic = props.num_rows === 'dynamic';
      const isDisabled = Boolean(props.disabled);

      // Toolbar
      const toolbar = document.createElement('div');
      toolbar.className = 'pv-editor-toolbar';
      const titleSpan = document.createElement('span');
      titleSpan.style.fontSize = '12px';
      titleSpan.style.color = 'var(--text-secondary)';
      titleSpan.textContent = `Interactive Data Editor (${rows.length} rows)`;
      toolbar.appendChild(titleSpan);

      if (isDynamic && !isDisabled) {
        const btnAdd = document.createElement('button');
        btnAdd.className = 'pv-df-btn';
        btnAdd.textContent = '➕ Add Row';
        btnAdd.addEventListener('click', (e) => {
          e.preventDefault();
          const newRow = columns.map((c) => {
            const cfg = columnConfig[c] || {};
            return cfg.default !== undefined ? cfg.default : '';
          });
          rows.push(newRow);
          dispatchUpdate();
          renderEditor();
        });
        toolbar.appendChild(btnAdd);
      }

      const tableWrapper = document.createElement('div');
      tableWrapper.className = 'pv-editor-table-wrapper';
      const table = document.createElement('table');
      table.className = 'pv-editor-table';

      function dispatchUpdate() {
        const payload = {
          columns: columns,
          data: rows,
          index: rows.map((_, i) => i),
        };
        sendWidgetEvent(id, payload);
      }

      function renderEditor() {
        table.innerHTML = '';
        const thead = document.createElement('thead');
        const trH = document.createElement('tr');

        columns.forEach((c) => {
          const th = document.createElement('th');
          th.textContent = (columnConfig[c] && columnConfig[c].label) || c;
          trH.appendChild(th);
        });

        if (isDynamic && !isDisabled) {
          const thAct = document.createElement('th');
          thAct.style.width = '40px';
          thAct.textContent = 'Action';
          trH.appendChild(thAct);
        }

        thead.appendChild(trH);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        rows.forEach((row, rIdx) => {
          const tr = document.createElement('tr');

          columns.forEach((colName, cIdx) => {
            const td = document.createElement('td');
            const cfg = columnConfig[colName] || {};
            const colType = cfg.type || (props.column_types && props.column_types[colName]) || 'text';
            const cellVal = row[cIdx];

            if (colType === 'checkbox') {
              const wrap = document.createElement('div');
              wrap.className = 'pv-cell-checkbox-wrapper';
              const chk = document.createElement('input');
              chk.type = 'checkbox';
              chk.className = 'pv-cell-checkbox';
              chk.setAttribute('data-widget-id', `${id}_r${rIdx}_c${cIdx}`);
              chk.checked = Boolean(cellVal);
              chk.disabled = isDisabled || cfg.disabled;
              chk.addEventListener('change', () => {
                rows[rIdx][cIdx] = chk.checked;
                dispatchUpdate();
              });
              wrap.appendChild(chk);
              td.appendChild(wrap);
            } else if (colType === 'selectbox') {
              const sel = document.createElement('select');
              sel.className = 'pv-cell-select';
              sel.setAttribute('data-widget-id', `${id}_r${rIdx}_c${cIdx}`);
              sel.disabled = isDisabled || cfg.disabled;
              const opts = cfg.options || [];
              opts.forEach((optVal) => {
                const opt = document.createElement('option');
                opt.value = optVal;
                opt.textContent = optVal;
                if (String(optVal) === String(cellVal)) opt.selected = true;
                sel.appendChild(opt);
              });
              sel.addEventListener('change', () => {
                rows[rIdx][cIdx] = sel.value;
                dispatchUpdate();
              });
              td.appendChild(sel);
            } else {
              const inp = document.createElement('input');
              inp.className = 'pv-cell-input';
              inp.setAttribute('data-widget-id', `${id}_r${rIdx}_c${cIdx}`);
              inp.type = colType === 'number' ? 'number' : 'text';
              inp.value = cellVal !== null && cellVal !== undefined ? cellVal : '';
              inp.disabled = isDisabled || cfg.disabled;
              if (cfg.min_value !== undefined) inp.min = cfg.min_value;
              if (cfg.max_value !== undefined) inp.max = cfg.max_value;
              if (cfg.step !== undefined) inp.step = cfg.step;

              const onCommit = () => {
                const updatedVal = colType === 'number' ? (inp.value === '' ? null : parseFloat(inp.value)) : inp.value;
                if (rows[rIdx][cIdx] !== updatedVal) {
                  rows[rIdx][cIdx] = updatedVal;
                  dispatchUpdate();
                }
              };

              inp.addEventListener('blur', onCommit);
              inp.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                  inp.blur();
                }
              });

              td.appendChild(inp);
            }

            tr.appendChild(td);
          });

          if (isDynamic && !isDisabled) {
            const tdAct = document.createElement('td');
            tdAct.style.textAlign = 'center';
            const btnDel = document.createElement('button');
            btnDel.className = 'pv-row-del-btn';
            btnDel.textContent = '🗑️';
            btnDel.title = 'Delete row';
            btnDel.addEventListener('click', (e) => {
              e.preventDefault();
              rows.splice(rIdx, 1);
              dispatchUpdate();
              renderEditor();
            });
            tdAct.appendChild(btnDel);
            tr.appendChild(tdAct);
          }

          tbody.appendChild(tr);
        });

        table.appendChild(tbody);
      }

      renderEditor();
      tableWrapper.appendChild(table);
      container.appendChild(toolbar);
      container.appendChild(tableWrapper);
      return container;
    }

    if (type === 'json_viewer') {
      const container = document.createElement('div');
      container.className = 'pv-json-viewer';
      container.id = id;

      const rawJson = props.raw_json || '{}';
      const expandedInit = props.expanded !== undefined ? props.expanded : true;

      // Copy Button
      const header = document.createElement('div');
      header.className = 'pv-json-header';
      const copyBtn = document.createElement('button');
      copyBtn.className = 'pv-json-copy-btn';
      copyBtn.textContent = '📋 Copy JSON';
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(rawJson);
        copyBtn.textContent = '✅ Copied!';
        setTimeout(() => {
          copyBtn.textContent = '📋 Copy JSON';
        }, 1500);
      });
      header.appendChild(copyBtn);
      container.appendChild(header);

      // JSON Tree
      const tree = document.createElement('div');
      tree.className = 'pv-json-tree';

      try {
        const parsed = JSON.parse(rawJson);
        tree.appendChild(buildJsonTreeNode(null, parsed, expandedInit, 0));
      } catch (e) {
        const pre = document.createElement('pre');
        pre.textContent = rawJson;
        tree.appendChild(pre);
      }

      container.appendChild(tree);
      return container;
    }

    if (type === 'progress') {
      const wrapper = document.createElement('div');
      wrapper.className = 'pv-progress-wrapper';
      wrapper.id = id;

      const pct = Math.max(0, Math.min(100, props.value || 0));

      const infoRow = document.createElement('div');
      infoRow.className = 'pv-progress-info';

      const labelSpan = document.createElement('span');
      labelSpan.className = 'pv-progress-label';
      labelSpan.textContent = props.text || '';

      const pctSpan = document.createElement('span');
      pctSpan.className = 'pv-progress-pct';
      pctSpan.textContent = `${pct}%`;

      infoRow.appendChild(labelSpan);
      infoRow.appendChild(pctSpan);

      const track = document.createElement('div');
      track.className = 'pv-progress-track';

      const fill = document.createElement('div');
      fill.className = 'pv-progress-fill-bar';
      fill.style.width = `${pct}%`;

      track.appendChild(fill);
      wrapper.appendChild(infoRow);
      wrapper.appendChild(track);
      return wrapper;
    }

    if (type === 'spinner') {
      const wrapper = document.createElement('div');
      wrapper.className = 'pv-spinner-wrapper';
      wrapper.id = id;

      const ring = document.createElement('div');
      ring.className = 'pv-spinner-ring';

      const text = document.createElement('span');
      text.className = 'pv-spinner-text';
      text.textContent = props.text || 'In progress...';

      wrapper.appendChild(ring);
      wrapper.appendChild(text);
      return wrapper;
    }

    if (type === 'toast') {
      triggerToast(props.body || '', props.icon || '💬');
      const placeholder = document.createElement('span');
      placeholder.id = id;
      placeholder.style.display = 'none';
      return placeholder;
    }

    if (type === 'balloons') {
      triggerBalloons();
      const placeholder = document.createElement('span');
      placeholder.id = id;
      placeholder.style.display = 'none';
      return placeholder;
    }

    if (type === 'snow') {
      triggerSnow();
      const placeholder = document.createElement('span');
      placeholder.id = id;
      placeholder.style.display = 'none';
      return placeholder;
    }

    if (type === 'exception') {
      const card = document.createElement('div');
      card.className = 'pv-exception-card';
      card.id = id;

      const header = document.createElement('div');
      header.className = 'pv-exception-header';
      header.textContent = `🛑 ${props.error_type || 'Exception'}: ${props.message || ''}`;

      const tbBox = document.createElement('pre');
      tbBox.className = 'pv-exception-traceback-box';
      tbBox.textContent = props.traceback || '';

      card.appendChild(header);
      card.appendChild(tbBox);
      return card;
    }

    if (type === 'image') {
      const container = document.createElement('div');
      container.className = props.is_gallery ? 'pv-image-grid' : 'pv-image-container';
      container.id = id;

      if (props.width) {
        container.style.maxWidth = props.width;
      } else if (!props.use_container_width) {
        container.style.maxWidth = 'fit-content';
      }

      (props.items || []).forEach((item) => {
        const card = document.createElement('div');
        card.className = 'pv-image-card';

        const img = document.createElement('img');
        img.className = 'pv-image-element';
        img.src = item.src;
        img.alt = item.caption || 'PyView Image';
        img.loading = 'lazy';

        card.appendChild(img);

        if (item.caption) {
          const cap = document.createElement('div');
          cap.className = 'pv-image-caption';
          cap.textContent = item.caption;
          card.appendChild(cap);
        }

        container.appendChild(card);
      });

      return container;
    }

    if (type === 'audio') {
      const container = document.createElement('div');
      container.className = 'pv-audio-container';
      container.id = id;

      const audioEl = document.createElement('audio');
      audioEl.className = 'pv-audio-element';
      audioEl.controls = true;
      audioEl.src = props.src;
      if (props.loop) audioEl.loop = true;
      if (props.autoplay) audioEl.autoplay = true;

      if (props.start_time) {
        audioEl.currentTime = props.start_time;
      }

      container.appendChild(audioEl);
      return container;
    }

    if (type === 'video') {
      const container = document.createElement('div');
      container.className = 'pv-video-container';
      container.id = id;

      if (props.embed_type === 'youtube' || props.embed_type === 'vimeo') {
        const iframe = document.createElement('iframe');
        iframe.className = 'pv-video-iframe';
        iframe.src = props.src;
        iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        iframe.allowFullscreen = true;
        iframe.frameBorder = '0';
        container.appendChild(iframe);
      } else {
        const videoEl = document.createElement('video');
        videoEl.className = 'pv-video-element';
        videoEl.controls = true;
        videoEl.src = props.src;
        if (props.loop) videoEl.loop = true;
        if (props.autoplay) videoEl.autoplay = true;
        if (props.muted) videoEl.muted = true;

        if (props.start_time) {
          videoEl.currentTime = props.start_time;
        }

        container.appendChild(videoEl);
      }

      return container;
    }

    if (type === 'logo') {
      const container = document.createElement('div');
      container.className = 'pv-logo-container';
      container.id = id;

      const img = document.createElement('img');
      img.className = 'pv-logo-img';
      img.src = props.image;
      img.alt = 'Logo';

      if (props.link) {
        const a = document.createElement('a');
        a.href = props.link;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.appendChild(img);
        container.appendChild(a);
      } else {
        container.appendChild(img);
      }

      return container;
    }

    if (type === 'pdf') {
      const container = document.createElement('div');
      container.className = 'pv-pdf-container';
      container.id = id;
      container.style.height = props.height || '500px';
      container.style.width = props.width || '100%';

      const iframe = document.createElement('iframe');
      iframe.className = 'pv-pdf-frame';
      iframe.src = props.src;
      iframe.title = 'PDF Viewer';

      container.appendChild(iframe);
      return container;
    }

    if (type === 'divider') {
      const hr = document.createElement('hr');
      hr.className = 'pv-divider';
      hr.id = id;
      return hr;
    }

    // Fallback for unknown widget
    const unknown = document.createElement('div');
    unknown.className = 'pv-unknown-widget';
    unknown.textContent = `[Unknown widget type: ${type}]`;
    return unknown;
  }

  function buildJsonTreeNode(key, value, expanded, depth) {
    const row = document.createElement('div');
    row.style.marginLeft = `${depth * 14}px`;

    const isObject = value !== null && typeof value === 'object';
    const isArray = Array.isArray(value);

    if (isObject) {
      const headerRow = document.createElement('div');
      headerRow.className = 'pv-json-row';

      const toggle = document.createElement('span');
      toggle.className = 'pv-json-toggle';
      toggle.textContent = expanded ? '▼' : '▶';

      headerRow.appendChild(toggle);

      if (key !== null) {
        const keySpan = document.createElement('span');
        keySpan.className = 'pv-json-key';
        keySpan.textContent = `"${key}": `;
        headerRow.appendChild(keySpan);
      }

      const bracketSpan = document.createElement('span');
      bracketSpan.style.color = 'var(--text-muted)';
      const keys = Object.keys(value);
      bracketSpan.textContent = isArray ? `[ ${keys.length} items ]` : `{ ${keys.length} keys }`;
      headerRow.appendChild(bracketSpan);
      row.appendChild(headerRow);

      const childrenContainer = document.createElement('div');
      childrenContainer.style.display = expanded ? 'block' : 'none';

      keys.forEach((k) => {
        childrenContainer.appendChild(buildJsonTreeNode(k, value[k], expanded, depth + 1));
      });

      row.appendChild(childrenContainer);

      toggle.addEventListener('click', () => {
        const isOpen = childrenContainer.style.display !== 'none';
        childrenContainer.style.display = isOpen ? 'none' : 'block';
        toggle.textContent = isOpen ? '▶' : '▼';
      });
    } else {
      const valRow = document.createElement('div');
      valRow.className = 'pv-json-row';
      valRow.style.paddingLeft = '14px';

      if (key !== null) {
        const keySpan = document.createElement('span');
        keySpan.className = 'pv-json-key';
        keySpan.textContent = `"${key}": `;
        valRow.appendChild(keySpan);
      }

      const valSpan = document.createElement('span');
      if (typeof value === 'string') {
        valSpan.className = 'pv-json-str';
        valSpan.textContent = `"${value}"`;
      } else if (typeof value === 'number') {
        valSpan.className = 'pv-json-num';
        valSpan.textContent = String(value);
      } else if (typeof value === 'boolean') {
        valSpan.className = 'pv-json-bool';
        valSpan.textContent = String(value);
      } else if (value === null) {
        valSpan.className = 'pv-json-null';
        valSpan.textContent = 'null';
      } else {
        valSpan.textContent = String(value);
      }
      valRow.appendChild(valSpan);
      row.appendChild(valRow);
    }

    return row;
  }

  function triggerToast(body, icon) {
    let dock = document.getElementById('pv-toast-dock');
    if (!dock) {
      dock = document.createElement('div');
      dock.id = 'pv-toast-dock';
      document.body.appendChild(dock);
    }

    const card = document.createElement('div');
    card.className = 'pv-toast-card';

    const iconEl = document.createElement('span');
    iconEl.className = 'pv-toast-icon';
    iconEl.textContent = icon || '💬';

    const bodyEl = document.createElement('div');
    bodyEl.className = 'pv-toast-body';
    bodyEl.textContent = body;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'pv-toast-close';
    closeBtn.textContent = '✕';

    card.appendChild(iconEl);
    card.appendChild(bodyEl);
    card.appendChild(closeBtn);
    dock.appendChild(card);

    const dismiss = () => {
      card.classList.add('pv-toast-exit');
      setTimeout(() => {
        if (card.parentNode) card.parentNode.removeChild(card);
      }, 250);
    };

    closeBtn.addEventListener('click', dismiss);
    setTimeout(dismiss, 4000);
  }

  function triggerBalloons() {
    const overlay = document.createElement('div');
    overlay.className = 'pv-celebrate-overlay';
    document.body.appendChild(overlay);

    const colors = ['#ff4b4b', '#ffa421', '#21c354', '#00d4b2', '#1c83e1', '#803df5', '#ff72d2'];
    const count = 30;

    for (let i = 0; i < count; i++) {
      const balloon = document.createElement('div');
      balloon.className = 'pv-balloon-item';
      const color = colors[i % colors.length];
      balloon.style.backgroundColor = color;
      const left = Math.random() * 92 + 4; // 4% - 96%
      balloon.style.left = `${left}%`;
      const delay = Math.random() * 1.5;
      const duration = 3.5 + Math.random() * 1.5;
      balloon.style.animationDelay = `${delay}s`;
      balloon.style.animationDuration = `${duration}s`;
      overlay.appendChild(balloon);
    }

    setTimeout(() => {
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
    }, 5500);
  }

  function triggerSnow() {
    const overlay = document.createElement('div');
    overlay.className = 'pv-celebrate-overlay';
    document.body.appendChild(overlay);

    const flakes = ['❄', '❅', '❆', '•'];
    const count = 45;

    for (let i = 0; i < count; i++) {
      const flake = document.createElement('div');
      flake.className = 'pv-snowflake-item';
      flake.textContent = flakes[i % flakes.length];
      const left = Math.random() * 96 + 2;
      flake.style.left = `${left}%`;
      const size = 12 + Math.random() * 18;
      flake.style.fontSize = `${size}px`;
      const delay = Math.random() * 2.0;
      const duration = 3.5 + Math.random() * 2.0;
      flake.style.animationDelay = `${delay}s`;
      flake.style.animationDuration = `${duration}s`;
      overlay.appendChild(flake);
    }

    setTimeout(() => {
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
    }, 6000);
  }

  // Event Listeners
  btnRerun.addEventListener('click', () => {
    sendMessage({ type: 'rerun' });
  });

  btnDismissError.addEventListener('click', () => {
    hideError();
  });

  if (btnToggleSidebar && sidebarRoot) {
    btnToggleSidebar.addEventListener('click', () => {
      sidebarRoot.style.display = sidebarRoot.style.display === 'none' ? 'flex' : 'none';
    });
  }

  // Shortcut: Ctrl+R / Cmd+R inside page triggers PyView rerun
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'r' && !e.shiftKey) {
      e.preventDefault();
      sendMessage({ type: 'rerun' });
    }
  });

  // Start connection
  connect();
})();
