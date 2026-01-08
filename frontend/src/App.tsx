import { useEffect, useState } from "react";
import {
  livenessApiHealthLivenessGet,
} from "./client";


export function App() {

  const [getIsLive, setIsLive]= useState<boolean>(false)


  useEffect(() => {
    livenessApiHealthLivenessGet().then(response => {
      if(!response.error) {
        console.log(response.data?.message)
        setIsLive(true)
      }
    })
  })

  return <>
     <h1>Backlog Boss</h1>
     <p>Is the app live? {getIsLive ? "Yes" : "No :("}</p>
  </>
}
