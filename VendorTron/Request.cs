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

namespace VendorTron
{
    public class Request
    {
        public String type;
        public String vendId;

        public static Request LogOut()
        {
            Request request = new Request();
            request.type = "log out";
            return request;
        }

        public static Request Vend(String vendId)
        {
            Request request = new Request();
            request.type = "vend";
            request.vendId = vendId;
            return request;
        }
    }
}
