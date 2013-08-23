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
using Newtonsoft.Json;

namespace VendorTron
{
    public class Request
    {
        public String type;
        public String vendId;
        public String key;

        private static readonly JsonSerializerSettings JSONSettings = new JsonSerializerSettings
        { NullValueHandling = NullValueHandling.Ignore };

        private Request(String type)
        {
            this.type = type;
        }

        public static Request LogOut()
        {
            return new Request("log out");
        }

        public static Request Vend(String vendId)
        {
            Request request = new Request("vend");
            request.vendId = vendId;
            return request;
        }

        public static Request Inventory()
        {
            return new Request("inventory");
        }
        public static Request Inventory(String key)
        {
            Request request = new Request("inventory");
            request.key = key;
            return request;
        }
        public String ToJSON()
        {
            return JsonConvert.SerializeObject(this, Formatting.None, Request.JSONSettings);
        }
    }
}
