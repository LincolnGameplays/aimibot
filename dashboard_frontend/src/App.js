import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import io from 'socket.io-client';

const socket = io('http://localhost:8000', { path: '/ws/socket.io' }); // Conecte ao seu backend FastAPI

function App() {
  const [sales, setSales] = useState([]);

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Conectado ao servidor WebSocket!');
    });

    socket.on('sale_created', (data) => {
      console.log('Nova venda recebida:', data);
      setSales((prevSales) => [...prevSales, { ...data, id: Date.now() }]);
      const audio = new Audio('/sounds/sale.mp3'); // Caminho para o seu som de venda
      audio.play();

      // Remove a notificação após alguns segundos
      setTimeout(() => {
        setSales((prevSales) => prevSales.filter((sale) => sale.id !== data.id));
      }, 5000); // Notificação desaparece após 5 segundos
    });

    socket.on('disconnect', () => {
      console.log('Desconectado do servidor WebSocket.');
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      <h1 className="text-5xl font-bold mb-8 text-purple-400">AimiAI Dashboard</h1>
      <p className="text-lg text-gray-300">Aguardando novas vendas...</p>

      <div className="fixed top-4 right-4 z-50 space-y-4">
        <AnimatePresence>
          {sales.map((sale) => (
            <motion.div
              key={sale.id}
              initial={{ opacity: 0, x: 300 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 300 }}
              transition={{ duration: 0.5 }}
              className="bg-green-600 p-4 rounded-lg shadow-lg flex items-center space-x-4"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-8 w-8 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2-1.343-2-3-2z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <div>
                <h3 className="text-xl font-bold">Nova Venda! 🎉</h3>
                <p className="text-sm">
                  Produto: {sale.product} - Valor: {sale.amount}
                </p>
                <p className="text-xs">Comprador: {sale.user}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;
