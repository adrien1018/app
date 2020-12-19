import React, {useEffect, useRef, useState} from "react"

import mixpanel from "mixpanel-browser"

import {BackButton, RefreshButton} from "../components/utils/util_buttons"
import {computer_analyses} from "../analyses/all_analyses"
import ComputerHeaderCard from "../analyses/computers/computer_header/card"
import {Footer} from '../components/utils/footer'
import CACHE from "../cache/cache"
import useWindowDimensions from "../utils/window_dimensions"
import {Status} from "../models/status"


interface RunProps {
    location: any
}

function ComputerView(props: RunProps) {
    const params = new URLSearchParams(props.location.search)
    const computerUUID = params.get('computer_uuid') as string
    const statusCache = CACHE.getComputerStatus(computerUUID)

    const [status, setStatus] = useState(null as unknown as Status)

    const {width: windowWidth} = useWindowDimensions()
    const actualWidth = Math.min(800, windowWidth)

    //TODO should create from a loop
    let refreshArray: any[] = [
        useRef(null) as any,
        useRef(null) as any,
        useRef(null) as any,
        useRef(null) as any,
        useRef(null) as any,
    ]

    let lastUpdated: number = 0

    useEffect(() => {
        async function load() {
            for (let i = 0; i < computer_analyses.length; i++) {
                if (refreshArray[i].current) {
                    refreshArray[i].current.load()
                }
            }

            setStatus(await statusCache.get())
            if (status && !status.isRunning) {
                clearInterval(interval)
            }
        }

        load().then()
        let interval = setInterval(load, 2 * 60 * 1000)
        return () => clearInterval(interval)
    }, [statusCache, refreshArray, status])

    useEffect(() => {
        mixpanel.track('Computer View', {uuid: computerUUID})
    }, [computerUUID])

    // call when load, 2 minutes interval and when refresh button clicks
    function onRefresh() {
        let oldest = (new Date()).getTime()

        for (let i = 0; i < computer_analyses.length; i++) {
            if (refreshArray[i].current) {
                refreshArray[i].current.refresh()

                if (refreshArray[i].current.lastUpdated < oldest) {
                    oldest = refreshArray[i].current.lastUpdated
                }
            }
        }

        lastUpdated = oldest
    }

    return <div className={'run page'} style={{width: actualWidth}}>
        <div className={'flex-container'}>
            <BackButton parent={'Computer View'}/>
            {status && status.isRunning && <RefreshButton onButtonClick={onRefresh} parent={'Computer View'}/>}
        </div>
        <ComputerHeaderCard uuid={computerUUID} width={actualWidth} lastUpdated={lastUpdated}/>
        {computer_analyses.map((analysis, i) => {
            return <analysis.card key={i} uuid={computerUUID} width={actualWidth}
                                  refreshRef={refreshArray[i]}/>
        })}
        <Footer/>
    </div>
}

export default ComputerView