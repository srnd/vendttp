using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MatrixBillAcceptor
{
    internal class Bitmask
    {
        private List<bool> bits = new List<bool>();

        public void Add(params bool[] v)
        {
            foreach (bool b in v)
            {
                bits.Add(b);
            }
        }

        public void Add(byte v)
        {
            for (int i = 0; i < 8; i++)
            {
                bool res = ((v & (byte)Math.Pow(2, i)) != 0);
                bits.Add(res);
            }
        }

        public static implicit operator byte[](Bitmask b)
        {
            int bytes = b.bits.Count / 8;
            if ((b.bits.Count % 8) != 0) bytes++;
            byte[] arr2 = new byte[bytes];
            int bitIndex = 0, byteIndex = 0;
            for (int i = 0; i < b.bits.Count; i++)
            {
                if (b.bits[i])
                {
                    arr2[byteIndex] |= (byte)(((byte)1) << bitIndex);
                }
                bitIndex++;
                if (bitIndex == 8)
                {
                    bitIndex = 0;
                    byteIndex++;
                }
            }

            return arr2;
        }
    }
}
