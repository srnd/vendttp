using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace ConsoleApplication1
{
    class Program
    {
        static void Main(string[] args)
        {
            SocketClient client = new SocketClient();
            client.Connect("192.168.0.4", 8636);
            client.Send("testing");
            client.Close();
        }
    }
}
