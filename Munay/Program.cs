using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MatrixBillAcceptor;
using System.Net;
using System.Net.Sockets;
using System.Threading;

namespace Munay
{
    class Listener
    {
        Boolean is_running = true;
        NetworkStream stream;
        BillAcceptor acceptor;
        public Listener(NetworkStream stream, BillAcceptor acceptor)
        {
            this.stream = stream;
            this.acceptor = acceptor;
        }
        public void Listen()
        {
            while (is_running)
            {
                if (stream.DataAvailable)
                {
                    Byte[] data = new Byte[256];
                    String responseData = String.Empty;
                    Int32 bytes = stream.Read(data, 0, data.Length);
                    responseData = System.Text.Encoding.ASCII.GetString(data, 0, bytes);

                    if (responseData == "enable")
                    {
                        acceptor.Enabled = true;
                        Console.WriteLine("enabled");
                    }
                    else if (responseData == "disable")
                    {
                        acceptor.Enabled = false;
                        Console.WriteLine("disabled");
                    }
                    else Console.WriteLine("anomaly received: " + responseData);
                }
                else
                {
                    //Sleep?
                }
            }
        }
        public void Stop()
        {
            is_running = false;
        }
    }

    class Program
    {
        static NetworkStream stream;
        static void Main(string[] args)
        {
            TcpClient sockish = new TcpClient("localhost", 8637);
            stream = sockish.GetStream();

            BillAcceptor acceptor = new BillAcceptor();

            acceptor.BillStacked += new BillStackedEvent(acceptor_BillStacked);

            acceptor.AcceptOnes = true;
            acceptor.AcceptFives = true;
            acceptor.AcceptTens = true;
            acceptor.AcceptTwenties = true;
            acceptor.AcceptHundreds = true;
            acceptor.Enabled = false;

            Listener l = new Listener(stream, acceptor);
            Thread thread = new Thread(new ThreadStart(l.Listen));
            thread.Start();
        }
        static void acceptor_BillStacked(BillAcceptor acceptor, int bill)
        {
            Console.WriteLine("Bill Stacked: $" + bill.ToString());
            Byte[] data = System.Text.Encoding.ASCII.GetBytes(bill.ToString());
            stream.Write(data, 0, data.Length);
        }
    }
}
