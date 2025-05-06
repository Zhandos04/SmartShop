document.addEventListener('DOMContentLoaded', function() {
    // Элементы интерфейса
    const openAIChatBtn = document.getElementById('openAIChat');
    const closeAIChatBtn = document.getElementById('closeAIChat');
    const aiAssistantChat = document.getElementById('aiAssistantChat');
    const aiChatMessages = document.getElementById('aiChatMessages');
    const aiMessageInput = document.getElementById('aiMessageInput');
    const sendAIMessageBtn = document.getElementById('sendAIMessage');
    
    // WebSocket соединение
    let aiSocket = null;
    let conversationId = localStorage.getItem('aiConversationId');
    
    // Функция для открытия чата с ИИ
    function openAIChat() {
        aiAssistantChat.style.display = 'flex';
        
        // Если нет ID диалога, создаем новый
        if (!conversationId) {
            fetch('/aisha/create_conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                conversationId = data.conversation_id;
                localStorage.setItem('aiConversationId', conversationId);
                connectWebSocket();
            });
        } else {
            // Если ID диалога есть, загружаем историю
            fetch(`/aisha/get_conversation_history/${conversationId}/`)
            .then(response => {
                if (!response.ok) {
                    // Если диалог не найден, создаем новый
                    localStorage.removeItem('aiConversationId');
                    openAIChat();
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data) {
                    // Очищаем историю сообщений
                    aiChatMessages.innerHTML = '';
                    
                    // Добавляем сообщения из истории
                    data.messages.forEach(msg => {
                        const messageClass = msg.role === 'user' ? 'user-message' : 'ai-message';
                        addMessageToChat(msg.content, messageClass);
                    });
                    
                    // Прокручиваем до последнего сообщения
                    aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
                    
                    // Подключаемся к WebSocket
                    connectWebSocket();
                }
            });
        }
    }
    
    // Подключение к WebSocket
    function connectWebSocket() {
        if (aiSocket) {
            aiSocket.close();
        }
        
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${wsProtocol}${window.location.host}/ws/aisha/${conversationId}/`;
        
        aiSocket = new WebSocket(wsUrl);
        
        aiSocket.onopen = function(e) {
            console.log('WebSocket соединение установлено');
        };
        
        aiSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            const messageClass = data.role === 'user' ? 'user-message' : 'ai-message';
            addMessageToChat(data.message, messageClass);
            
            // Прокручиваем до последнего сообщения
            aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
        };
        
        aiSocket.onclose = function(e) {
            console.log('WebSocket соединение закрыто');
        };
        
        aiSocket.onerror = function(e) {
            console.error('WebSocket ошибка:', e);
        };
    }
    
    // Функция для закрытия чата с ИИ
    function closeAIChat() {
        aiAssistantChat.style.display = 'none';
        
        // Закрываем WebSocket соединение
        if (aiSocket) {
            aiSocket.close();
            aiSocket = null;
        }
    }
    
    // Функция для отправки сообщения
    function sendAIMessage() {
        const message = aiMessageInput.value.trim();
        if (message && aiSocket && aiSocket.readyState === WebSocket.OPEN) {
            // Отправка сообщения через WebSocket
            aiSocket.send(JSON.stringify({
                'message': message
            }));
            
            // Очищаем поле ввода
            aiMessageInput.value = '';
        }
    }
    
    // Функция добавления сообщения в чат
    function addMessageToChat(message, messageClass) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageClass}`;
        messageElement.innerHTML = `<div class="message-content">${message}</div>`;
        aiChatMessages.appendChild(messageElement);
    }
    
    // Получение CSRF-токена из cookies
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
    
    // События
    openAIChatBtn.addEventListener('click', openAIChat);
    closeAIChatBtn.addEventListener('click', closeAIChat);
    sendAIMessageBtn.addEventListener('click', sendAIMessage);
    
    aiMessageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendAIMessage();
        }
    });
    
    // Периодически проверяем, не завершена ли сессия
    setInterval(function() {
        if (aiSocket && aiSocket.readyState !== WebSocket.OPEN) {
            if (aiAssistantChat.style.display !== 'none') {
                connectWebSocket();
            }
        }
    }, 5000);
    
    // Случайные всплывающие подсказки от ИИ
    function showRandomAIHint() {
        if (aiAssistantChat.style.display === 'none') {
            const hints = [
                'Привет, нужна помощь?',
                'Посоветовать что-то?',
                'Найти что-нибудь?',
                'Я могу помочь выбрать подарок!',
                'Хотите узнать о новинках?'
            ];
            
            // Создаем всплывающую подсказку
            const hintElement = document.createElement('div');
            hintElement.className = 'ai-hint';
            hintElement.innerHTML = hints[Math.floor(Math.random() * hints.length)];
            hintElement.style.position = 'absolute';
            hintElement.style.bottom = '70px';
            hintElement.style.right = '0';
            hintElement.style.backgroundColor = '#fff';
            hintElement.style.padding = '10px 15px';
            hintElement.style.borderRadius = '10px';
            hintElement.style.boxShadow = '0 3px 10px rgba(0, 0, 0, 0.2)';
            hintElement.style.maxWidth = '250px';
            hintElement.style.cursor = 'pointer';
            
            // Добавляем подсказку на страницу
            document.querySelector('.ai-assistant-wrapper').appendChild(hintElement);
            
            // По клику на подсказку открываем чат
            hintElement.addEventListener('click', function() {
                openAIChat();
                hintElement.remove();
            });
            
            // Удаляем подсказку через 5 секунд
            setTimeout(() => {
                if (hintElement.parentNode) {
                    hintElement.remove();
                }
            }, 5000);
        }
    }
    
    // Показываем случайную подсказку через 30-60 секунд после загрузки страницы
    setTimeout(showRandomAIHint, Math.random() * 30000 + 30000);
});