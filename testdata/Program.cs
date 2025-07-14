using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace C005
{
    class Program
    {
        static void Main(string[] args)
        {
            // M(入力する行数)の入力
            Console.Write("入力するIPv4の個数 : ");
            int M = int.Parse(Console.ReadLine());
            if(1<=M && M<=100)
            {
                // IPアドレスの入力
                Console.WriteLine("IPv4の入力");
                for(int i=1;i<=M;i++)
                {
                    string ipv4 = Console.ReadLine();
                    //取得したIPv4を'.'で分割
                    string[] arr = ipv4.Split('.');
                    
                    //arr[]をint型に変換
                    bool retA = int.TryParse(arr[0], out int a);
                    bool retB = int.TryParse(arr[1], out int b);
                    bool retC = int.TryParse(arr[2], out int c);
                    bool retD = int.TryParse(arr[3], out int d);
                    
                    //変換できなかった場合のエラー表示。
                    if(retA == false || retB == false || retC == false || retD == false)
                    {
                        Console.WriteLine("False");
                    }
                    //分割された文字列の配列の要素数が4つ([0]~[3])以外のときFalse
                    else if(arr.Length != 4)
                    {
                        Console.WriteLine("False");
                    }
                    //分割された文字列の、配列内の整数が０～２５５の場合True
                    else if(0<=a && a<=255 && 0<=b && b<=255 && 0<=c && c<=255 && 0<=d && d<=255)
                    {
                        Console.WriteLine("True");
                    }
                    else
                    {
                        Console.WriteLine("False");
                    }
                }
            }
        }
    }
}

/*
    1．IPアドレスの数を入力
    2．(1．)で入力された数分だけIPアドレスを入力
    3．IPv4として正しいか判定（.区切りで0～255までの値が4区間に入っているか）
    4．IPv4として正しいのであれば、True、違う場合はFalseと出力
*/

/*
課題
・ドットの数が3つ未満のとき終了する。配列内に空ができたとみなされるから？
・最初にIPv4の個数を入力する値が正の整数じゃない場合終了する。
*/