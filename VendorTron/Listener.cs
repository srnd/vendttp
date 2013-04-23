using System;
using System.Net;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Ink;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;
using System.Net.Sockets;
using System.IO;
using System.Threading;

namespace Vendortron
{
    public class Listener
    {
        Boolean is_running = true;
        Stream stream;
        Action<String> Log;
        Action OnDisconnect;

        public Listener(Stream stream, Action<String> Log, Action OnDisconnect)
        {
            this.stream = stream;
            this.Log = Log;
            this.OnDisconnect = OnDisconnect;
        }

        public void Listen()
        {
            while (is_running)
            {
                if (stream.CanRead)
                {
                    Byte[] data = new Byte[256];
                    Int32 bytes = stream.Read(data, 0, data.Length);
                    String responseData = System.Text.Encoding.UTF8.GetString(data, 0, bytes);
                    if (responseData.Length == 0)
                    {
                        OnDisconnect();
                        is_running = false;
                    }
                    else
                    {
                        Log(responseData);
                    }
                }
                else
                {
                    Thread.Sleep(4);
                }
            }
        }

        public void Stop()
        {
            is_running = false;
        }
    }
}
