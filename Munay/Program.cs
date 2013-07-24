using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MatrixBillAcceptor;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.IO;

namespace Munay
{
    class Program
    {
        static MatrixBillAcceptor.MatrixBillAcceptor acceptor;
        static TcpClient sockish;
        static NetworkStream stream;

        static void Main(string[] args)
        {
            Console.WriteLine("Bill Acceptor controller for VendorTron 2000");

            InitAcceptor();

            while (true)
            {
                SafeAcceptor().Enabled = true;

                Console.WriteLine("Attempting to connect to server.");
                while (true)
                {
                    try
                    {
                        sockish = new TcpClient("localhost", 8637);
                        stream = sockish.GetStream();
                        break;
                    }
                    catch (SocketException)
                    {
                        Thread.Sleep(1000);
                        continue;
                    }
                }
                Console.WriteLine("Connected to server.");
                Listen();
            }
        }

        static public void InitAcceptor()
        {
            acceptor = new MatrixBillAcceptor.MatrixBillAcceptor();

            acceptor.BillStacked += new MatrixBillAcceptor.BillStackedEvent(acceptor_BillStacked);
            acceptor.AcceptOnes = true;
            acceptor.AcceptFives = true;
            acceptor.AcceptTens = true;
            acceptor.AcceptTwenties = true;
            acceptor.AcceptHundreds = true;
        }

        static MatrixBillAcceptor.MatrixBillAcceptor SafeAcceptor()
        {
            while (acceptor == null)
            {
                Thread.Sleep(50);
            }
            return acceptor;
        }

        static public void Listen()
        {
            NetworkStream stream = sockish.GetStream();
            while (true)
            {
                if (stream.CanRead)
                {
                    Byte[] data = new Byte[256];
                    String responseData = String.Empty;
                    Int32 bytes = 0;
                    try
                    {
                        bytes = stream.Read(data, 0, data.Length);
                    }
                    catch (IOException)
                    {
                        Console.WriteLine("Disconnected from server");
                        return;
                    }
                    responseData = System.Text.Encoding.ASCII.GetString(data, 0, bytes);

                    if (responseData.Length == 0)
                    {
                        Console.WriteLine("Disconnected");
                        return;
                    }
                    else if (responseData.Equals("enable\n"))
                    {
                        SafeAcceptor().Enabled = true;
                        Console.WriteLine("enabled");
                    }
                    else if (responseData.Equals("disable\n"))
                    {
                        SafeAcceptor().Enabled = false;
                        Console.WriteLine("disabled");
                    }
                    else
                        Console.WriteLine("message received: " + responseData);

                }
                else
                {
                    Console.WriteLine("Can't Read");
                }
                Thread.Sleep(500);
            }
        }

        static void acceptor_BillStacked(MatrixBillAcceptor.MatrixBillAcceptor acceptor, int bill)
        {
            Console.WriteLine("Bill Stacked: $" + bill.ToString());
            Byte[] data = System.Text.Encoding.ASCII.GetBytes(bill.ToString());
            if (stream != null && stream.CanWrite)
                stream.Write(data, 0, data.Length);
        }
    }
}
